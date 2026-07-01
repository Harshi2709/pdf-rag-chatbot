"""
Intent Classification Module
Determines user query intent to decide retrieval strategy
"""
from typing import Dict, List, Any, Optional
from llm.ollama_client import OllamaClient
from utils.logging_config import get_logger

logger = get_logger(__name__)


class IntentClassifier:
    """
    Classifies user queries into intent categories
    Uses LLM-based classification for accuracy
    """
    
    # Intent definitions
    INTENTS = {
        "document_qa": "User is asking a factual question about document content",
        "conversational_followup": "User is following up on previous conversation",
        "clarification": "User is asking to clarify or explain previous answer",
        "summarization": "User wants a summary of document or previous content",
        "comparison": "User wants to compare information across documents",
        "meta_question": "User is asking about the conversation itself or how AI works",
        "greeting": "User is greeting or making small talk",
        "feedback": "User is providing feedback on previous response"
    }
    
    CLASSIFICATION_PROMPT = """You are an intent classifier for a conversational document Q&A system.

Given a user query and conversation history, classify the query into ONE of these intents:

1. document_qa - Asking factual questions about document content
   Examples: "What does the PDF say about AI?", "Find revenue numbers"

2. conversational_followup - Following up on previous conversation with references
   Examples: "What about the second point?", "Can you elaborate on that?"

3. clarification - Asking to clarify or explain previous answer
   Examples: "What did you mean by that?", "Can you explain more clearly?"

4. summarization - Requesting a summary
   Examples: "Summarize that section", "Give me the key points"

5. comparison - Comparing information
   Examples: "Compare both PDFs", "What's the difference between X and Y?"

6. meta_question - Questions about the conversation or AI itself
   Examples: "Did you use the document?", "Why did you answer like that?"

7. greeting - Greetings or small talk
   Examples: "Hello", "Thanks", "Good job"

8. feedback - Providing feedback
   Examples: "That's wrong", "Good answer", "You misunderstood"

CONVERSATION HISTORY:
{history}

CURRENT QUERY:
{query}

IMPORTANT: Respond with ONLY the intent name (e.g., "document_qa"). No explanation."""
    
    def __init__(self, llm_client: Optional[OllamaClient] = None):
        """
        Initialize intent classifier
        
        Args:
            llm_client: LLM client for classification (uses Ollama by default)
        """
        self.llm_client = llm_client or OllamaClient()
    
    def classify(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Classify user query intent
        
        Args:
            query: User query to classify
            conversation_history: Recent conversation messages
        
        Returns:
            Dictionary with intent, confidence, and needs_retrieval flag
        """
        # Format conversation history
        history_str = self._format_history(conversation_history or [])
        
        # Build classification prompt
        prompt = self.CLASSIFICATION_PROMPT.format(
            history=history_str,
            query=query
        )
        
        # Get classification from LLM
        try:
            response = self.llm_client.generate(prompt, temperature=0.1)
            intent = response.strip().lower()
            
            # Validate intent
            if intent not in self.INTENTS:
                # Fallback: try to match partial
                for valid_intent in self.INTENTS:
                    if valid_intent in intent:
                        intent = valid_intent
                        break
                else:
                    intent = "document_qa"  # Default fallback
            
            # Determine if retrieval is needed
            needs_retrieval = self._should_retrieve(intent, query)
            
            return {
                "intent": intent,
                "description": self.INTENTS[intent],
                "needs_retrieval": needs_retrieval,
                "confidence": "high"  # LLM-based classification
            }
        
        except Exception as e:
            logger.exception("Intent classification error")
            # Fallback to rule-based
            return self._fallback_classification(query, conversation_history)
    
    def _should_retrieve(self, intent: str, query: str) -> bool:
        """
        Determine if retrieval is needed based on intent
        
        Args:
            intent: Classified intent
            query: User query
        
        Returns:
            Boolean indicating if retrieval is needed
        """
        # Intents that definitely need retrieval
        retrieval_intents = {
            "document_qa",
            "summarization",
            "comparison"
        }
        
        # Intents that might need retrieval
        conditional_intents = {
            "conversational_followup",
            "clarification"
        }
        
        if intent in retrieval_intents:
            return True
        
        if intent in conditional_intents:
            # Use simple heuristics
            doc_keywords = ["document", "pdf", "file", "report", "page"]
            return any(keyword in query.lower() for keyword in doc_keywords)
        
        # No retrieval for greetings, meta questions, feedback
        return False
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        for msg in history[-3:]:  # Last 3 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)
    
    def _fallback_classification(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Rule-based fallback classification
        Used if LLM classification fails
        """
        query_lower = query.lower()
        
        # Greeting patterns
        greetings = ["hi", "hello", "hey", "thanks", "thank you", "bye"]
        if any(g in query_lower for g in greetings) and len(query.split()) < 5:
            return {
                "intent": "greeting",
                "description": self.INTENTS["greeting"],
                "needs_retrieval": False,
                "confidence": "medium"
            }
        
        # Reference patterns (followup)
        references = ["that", "this", "it", "previous", "above", "earlier"]
        if any(ref in query_lower for ref in references) and len(conversation_history) > 0:
            return {
                "intent": "conversational_followup",
                "description": self.INTENTS["conversational_followup"],
                "needs_retrieval": True,
                "confidence": "medium"
            }
        
        # Summary patterns
        summary_words = ["summarize", "summary", "overview", "key points"]
        if any(word in query_lower for word in summary_words):
            return {
                "intent": "summarization",
                "description": self.INTENTS["summarization"],
                "needs_retrieval": True,
                "confidence": "high"
            }
        
        # Comparison patterns
        comparison_words = ["compare", "difference", "versus", "vs", "both"]
        if any(word in query_lower for word in comparison_words):
            return {
                "intent": "comparison",
                "description": self.INTENTS["comparison"],
                "needs_retrieval": True,
                "confidence": "high"
            }
        
        # Default to document QA
        return {
            "intent": "document_qa",
            "description": self.INTENTS["document_qa"],
            "needs_retrieval": True,
            "confidence": "low"
        }
