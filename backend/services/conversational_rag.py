"""
Conversational RAG Orchestrator
Integrates memory, intent classification, query rewriting, and RAG
"""
import time
from typing import Dict, List, Any, Optional
from services.memory_manager import MemoryManager, memory_manager
from services.intent_classifier import IntentClassifier
from services.query_rewriter import QueryRewriter
from retrieval.retriever import Retriever
from retrieval.metadata_retriever import MetadataRetriever
from services.query_router import QueryRouter
from llm.ollama_client import OllamaClient
from prompts.conversational_prompts import ConversationalRAGPrompt
from vectordb.chroma_client import ChromaDBClient
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConversationalRAG:
    """
    Orchestrates conversational RAG pipeline with memory and context awareness
    
    Pipeline:
    1. Conversation Memory → Retrieve session history
    2. Intent Classification → Determine query type
    3. Query Rewriting → Convert to standalone query
    4. Retrieval Decision → Decide if retrieval needed
    5. Document Retrieval → Get relevant chunks (if needed)
    6. Prompt Construction → Build context-aware prompt
    7. LLM Response → Generate answer
    8. Memory Update → Store interaction
    """
    
    def __init__(
        self,
        vector_db: ChromaDBClient,
        top_k: int = 5,
        model_name: str = "llama3",
        memory_manager: Optional[MemoryManager] = None
    ):
        """
        Initialize Conversational RAG
        
        Args:
            vector_db: Vector database client
            top_k: Number of documents to retrieve
            model_name: Ollama model name
            memory_manager: Memory manager instance
        """
        self.vector_db = vector_db
        self.top_k = top_k
        
        # Initialize components
        self.llm_client = OllamaClient(model_name=model_name)
        self.memory_manager = memory_manager or globals()['memory_manager']
        self.intent_classifier = IntentClassifier(llm_client=self.llm_client)
        self.query_rewriter = QueryRewriter(llm_client=self.llm_client)
        self.retriever = Retriever(vector_db=vector_db, top_k=top_k)
        self.metadata_retriever = MetadataRetriever(vector_db=vector_db, top_k=top_k)
        self.query_router = QueryRouter()
        self.prompt_template = ConversationalRAGPrompt()
    
    def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # ===== STAGE 1: CONVERSATION MEMORY =====
            logger.info("[Stage 1] Retrieving conversation memory...")
            
            # Get or create session
            if session_id:
                session = self.memory_manager.get_or_create_session(session_id)
            else:
                session_id = self.memory_manager.create_session()
                session = self.memory_manager.get_session(session_id)
            
            # Use provided chat history or retrieve from memory
            if chat_history:
                conversation_history = chat_history
            else:
                conversation_history = session.get_recent_messages(n=5)
            
            logger.debug("Session: %s, History length: %d", session_id, len(conversation_history))
            
            # ===== STAGE 2: INTENT CLASSIFICATION =====
            logger.info("[Stage 2] Classifying intent...")
            
            intent_result = self.intent_classifier.classify(
                query=query,
                conversation_history=conversation_history
            )
            
            detected_intent = intent_result["intent"]
            needs_retrieval = intent_result["needs_retrieval"]
            
            logger.debug("Intent: %s, Needs Retrieval: %s", detected_intent, needs_retrieval)
            
            # ===== STAGE 3: QUERY REWRITING =====
            logger.info("[Stage 3] Rewriting query...")
            
            rewrite_result = self.query_rewriter.rewrite(
                query=query,
                conversation_history=conversation_history,
                intent=detected_intent
            )
            
            rewritten_query = rewrite_result["rewritten_query"]
            was_rewritten = rewrite_result["was_rewritten"]
            
            logger.debug("Original query: %s", query)
            logger.debug("Rewritten query: %s", rewritten_query)
            logger.debug("Was rewritten: %s", was_rewritten)
            
            # ===== STAGE 4: RETRIEVAL DECISION =====
            logger.info("[Stage 4] Making retrieval decision...")
            
            # Check if vector DB has documents
            has_documents = self.vector_db.get_collection_count() > 0
            
            if not has_documents:
                # No documents uploaded yet
                answer = "No documents have been uploaded yet. Please upload a PDF document first to ask questions about it."
                
                # Store in memory
                self.memory_manager.add_message(session_id, "user", query)
                self.memory_manager.add_message(session_id, "assistant", answer)
                
                return {
                    "answer": answer,
                    "session_id": session_id,
                    "citations": [],
                    "retrieved_chunks": [],
                    "processing_time": f"{time.time() - start_time:.2f}s",
                    "debug_info": {
                        "intent": detected_intent,
                        "original_query": query,
                        "rewritten_query": rewritten_query,
                        "was_rewritten": was_rewritten,
                        "needs_retrieval": needs_retrieval,
                        "retrieval_performed": False,
                        "reason": "No documents in database"
                    } if debug else None
                }
            
            # Decide whether to retrieve
            should_retrieve = needs_retrieval and has_documents
            
            logger.debug("Should Retrieve: %s", should_retrieve)
            
            # ===== STAGE 5: DOCUMENT RETRIEVAL (CONDITIONAL) =====
            retrieved_docs = []
            context = ""
            citations = []
            routing_result = None
            
            if should_retrieve:
                logger.info("[Stage 5] Retrieving documents...")
                
                # Use query router to detect figure/table references
                routing_result = self.query_router.route_query(rewritten_query)
                logger.debug("Query routing: %s", routing_result['routing_strategy'])
                
                # Use metadata-aware retriever
                metadata_filters = routing_result.get('metadata_filters')
                retrieved_docs = self.metadata_retriever.retrieve(
                    query=rewritten_query,
                    metadata_filters=metadata_filters,
                    top_k=self.top_k
                )
                
                context = self.metadata_retriever.assemble_context(
                    retrieved_docs,
                    highlight_metadata=True
                )
                citations = self.metadata_retriever.extract_citations(retrieved_docs)
                
                logger.info("Retrieved %d chunks", len(retrieved_docs))
            else:
                logger.info("[Stage 5] Skipping retrieval (not needed for this intent)")
            
            # ===== STAGE 6: PROMPT CONSTRUCTION =====
            logger.info("[Stage 6] Building prompt...")
            
            # Format conversation history
            history_str = self.memory_manager.format_history_for_llm(
                session_id=session_id,
                n_recent=5
            )
            
            # Build appropriate prompt
            if should_retrieve:
                prompt = self.prompt_template.build_conversational_prompt(
                    question=query,  # Use original query in prompt
                    retrieved_context=context,
                    conversation_history=history_str,
                    use_retrieval=True
                )
            else:
                prompt = self.prompt_template.build_simple_prompt(
                    question=query,
                    conversation_history=history_str
                )
            
            # ===== STAGE 7: LLM RESPONSE =====
            logger.info("[Stage 7] Generating response...")
            
            # Adjust temperature based on intent
            temperature = 0.3 if detected_intent in ["document_qa", "comparison"] else 0.7
            
            answer = self.llm_client.generate(prompt, temperature=temperature)
            answer = answer.strip()
            
            # ===== STAGE 8: MEMORY UPDATE =====
            logger.info("[Stage 8] Updating memory...")
            
            self.memory_manager.add_message(session_id, "user", query)
            self.memory_manager.add_message(session_id, "assistant", answer)
            
            processing_time = time.time() - start_time
            logger.info("Total processing time: %.2fs", processing_time)
            
            avg_similarity = sum(doc.similarity_score for doc in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0.0
            confidence = round(min(0.99, 0.35 + 0.35 * min(1.0, len(citations) / 5.0) + 0.30 * avg_similarity), 2)

            # Build response
            response = {
                "answer": answer,
                "session_id": session_id,
                "citations": citations,
                "sources": citations,
                "confidence": confidence,
                "retrieved_chunks": [doc.to_dict() for doc in retrieved_docs],
                "processing_time": f"{processing_time:.2f}s",
                "metadata": {
                    "num_chunks_retrieved": len(retrieved_docs),
                    "model": self.llm_client.model_name,
                    "intent": detected_intent
                }
            }
            
            # Add debug information if requested
            if debug:
                response["debug_info"] = {
                    "intent": detected_intent,
                    "intent_description": intent_result["description"],
                    "original_query": query,
                    "rewritten_query": rewritten_query,
                    "was_rewritten": was_rewritten,
                    "needs_retrieval": needs_retrieval,
                    "retrieval_performed": should_retrieve,
                    "conversation_history_length": len(conversation_history),
                    "temperature": temperature,
                    "query_routing": routing_result if routing_result else None
                }
            
            return response
        
        except Exception as e:
            logger.exception("Error in conversational RAG pipeline")
            
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "session_id": session_id or "unknown",
                "citations": [],
                "retrieved_chunks": [],
                "processing_time": f"{time.time() - start_time:.2f}s",
                "error": str(e)
            }
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        session = self.memory_manager.get_session(session_id)
        
        if not session:
            return {
                "exists": False,
                "message": "Session not found"
            }
        
        return {
            "exists": True,
            "session_id": session_id,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
            "message_count": len(session.messages),
            "recent_messages": session.get_recent_messages(3)
        }
    
    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear conversation history for a session"""
        self.memory_manager.clear_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} cleared"
        }
