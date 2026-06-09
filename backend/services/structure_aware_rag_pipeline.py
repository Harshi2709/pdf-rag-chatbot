"""
Structure-Aware RAG Pipeline
Enhanced RAG workflow with document structure understanding
"""
import time
from typing import Dict, List, Any
from loaders.docling_loader import DoclingLoader, StructuredDocument
from chunking.structure_aware_splitter import StructureAwareSplitter
from embeddings.embedding_model import embedding_model
from vectordb.chroma_client import ChromaDBClient
from retrieval.metadata_retriever import MetadataRetriever
from services.query_router import QueryRouter
from llm.ollama_client import OllamaClient
from prompts.rag_prompt import RAGPromptTemplate


class StructureAwareRAGPipeline:
    """
    Structure-Aware RAG Pipeline
    
    Enhancements:
    - Docling-based PDF parsing
    - Structure-aware chunking
    - Figure/Table extraction
    - Metadata-aware retrieval
    - Query routing for figures/tables
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        top_k: int = 5,
        model_name: str = "llama3"
    ):
        """
        Initialize Structure-Aware RAG Pipeline
        
        Args:
            chunk_size: Maximum size of text chunks
            top_k: Number of documents to retrieve
            model_name: Ollama model name
        """
        self.chunk_size = chunk_size
        self.top_k = top_k
        
        # Initialize new components
        self.structure_splitter = StructureAwareSplitter(
            max_chunk_size=chunk_size,
            min_chunk_size=100
        )
        self.embedding_model = embedding_model
        self.vector_db = ChromaDBClient()
        self.metadata_retriever = MetadataRetriever(
            vector_db=self.vector_db,
            top_k=top_k
        )
        self.query_router = QueryRouter()
        self.llm_client = OllamaClient(model_name=model_name)
        self.prompt_template = RAGPromptTemplate()
    
    def ingest_pdf(self, file_path: str, upload_timestamp: str = None) -> Dict[str, Any]:
        """
        Structure-aware PDF ingestion pipeline
        
        Pipeline stages:
        1. Docling PDF Loading (structure extraction)
        2. Structure-Aware Chunking
        3. Embedding Generation
        4. Vector Storage with Metadata
        
        Args:
            file_path: Path to PDF file
            upload_timestamp: Timestamp of upload
        
        Returns:
            Ingestion status dictionary with structure metrics
        """
        start_time = time.time()
        
        try:
            # Stage 1: Structure-Aware PDF Loading
            print("\n=== Stage 1: Loading PDF with Docling ===")
            loader = DoclingLoader(file_path)
            structured_doc: StructuredDocument = loader.load()
            
            print(f"✓ Loaded: {structured_doc.filename}")
            print(f"  - Pages: {structured_doc.total_pages}")
            print(f"  - Title: {structured_doc.title or 'N/A'}")
            print(f"  - Elements: {len(structured_doc.elements)}")
            print(f"  - Figures: {len(structured_doc.get_figures())}")
            print(f"  - Tables: {len(structured_doc.get_tables())}")
            
            # Stage 2: Structure-Aware Chunking
            print("\n=== Stage 2: Structure-Aware Chunking ===")
            chunks = self.structure_splitter.create_chunks(structured_doc.elements)
            
            # Count chunk types
            chunk_types = {}
            for chunk in chunks:
                chunk_type = chunk.chunk_type
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print(f"✓ Created {len(chunks)} chunks:")
            for chunk_type, count in chunk_types.items():
                print(f"  - {chunk_type}: {count}")
            
            # Stage 3: Embedding Generation
            print("\n=== Stage 3: Generating Embeddings ===")
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_model.embed_texts(texts)
            print(f"✓ Generated {len(embeddings)} embeddings")
            
            # Stage 4: Vector Storage with Metadata
            print("\n=== Stage 4: Storing with Metadata ===")
            
            if upload_timestamp is None:
                from datetime import datetime
                upload_timestamp = datetime.now().isoformat()
            
            # Enrich metadata
            metadatas = []
            for chunk in chunks:
                metadata = chunk.metadata.copy()
                metadata["upload_timestamp"] = upload_timestamp
                metadata["chunk_type"] = chunk.chunk_type
                metadatas.append(metadata)
            
            ids = [chunk.chunk_id for chunk in chunks]
            
            # Store in vector DB
            self.vector_db.add_documents(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            processing_time = time.time() - start_time
            print(f"\n✓ Ingestion complete in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "filename": structured_doc.filename,
                "total_pages": structured_doc.total_pages,
                "total_chunks": len(chunks),
                "chunk_breakdown": chunk_types,
                "figures_extracted": len(structured_doc.get_figures()),
                "tables_extracted": len(structured_doc.get_tables()),
                "vector_db_count": self.vector_db.get_collection_count(),
                "processing_time": f"{processing_time:.2f}s",
                "upload_timestamp": upload_timestamp,
                "document_title": structured_doc.title
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "processing_time": f"{time.time() - start_time:.2f}s"
            }
    
    def query(self, question: str, debug: bool = False) -> Dict[str, Any]:
        """
        Structure-aware RAG query pipeline
        
        Pipeline stages:
        1. Query Routing (detect figures/tables)
        2. Metadata-Aware Retrieval
        3. Context Assembly
        4. Prompt Construction
        5. LLM Inference
        
        Args:
            question: User question
            debug: Include debug information
        
        Returns:
            Response dictionary with answer and metadata
        """
        start_time = time.time()
        
        try:
            # Stage 1: Query Routing
            print("\n=== Stage 1: Query Routing ===")
            routing_result = self.query_router.route_query(question)
            
            print(f"Query Type: {routing_result['query_type']}")
            print(f"Routing Strategy: {routing_result['routing_strategy']}")
            if routing_result['detected_entities']:
                print(f"Detected Entities: {routing_result['detected_entities']}")
            
            # Stage 2: Metadata-Aware Retrieval
            print("\n=== Stage 2: Metadata-Aware Retrieval ===")
            metadata_filters = routing_result.get('metadata_filters')
            
            retrieved_docs = self.metadata_retriever.retrieve(
                query=question,
                metadata_filters=metadata_filters,
                top_k=self.top_k
            )
            
            print(f"✓ Retrieved {len(retrieved_docs)} documents")
            
            # Stage 3: Context Assembly
            print("\n=== Stage 3: Assembling Context ===")
            context = self.metadata_retriever.assemble_context(
                retrieved_docs,
                highlight_metadata=True
            )
            
            # Stage 4: Prompt Construction
            print("\n=== Stage 4: Building Prompt ===")
            prompt = self.prompt_template.build_prompt(context, question)
            
            # Stage 5: LLM Inference
            print("\n=== Stage 5: Generating Response ===")
            answer = self.llm_client.generate(prompt, temperature=0.7)
            
            # Extract citations
            citations = self.metadata_retriever.extract_citations(retrieved_docs)
            
            processing_time = time.time() - start_time
            print(f"\n✓ Query complete in {processing_time:.2f}s")
            
            response = {
                "answer": answer.strip(),
                "citations": citations,
                "retrieved_chunks": [doc.to_dict() for doc in retrieved_docs],
                "processing_time": f"{processing_time:.2f}s",
                "metadata": {
                    "num_chunks_retrieved": len(retrieved_docs),
                    "model": self.llm_client.model_name,
                    "query_type": routing_result['query_type']
                }
            }
            
            # Add debug info if requested
            if debug:
                response["debug_info"] = {
                    "query_routing": routing_result,
                    "metadata_filters_applied": metadata_filters,
                    "chunk_types_retrieved": [
                        doc.metadata.get("chunk_type", "unknown")
                        for doc in retrieved_docs
                    ]
                }
            
            return response
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "retrieved_chunks": [],
                "processing_time": f"{time.time() - start_time:.2f}s",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "vector_db_count": self.vector_db.get_collection_count(),
            "chunk_size": self.chunk_size,
            "top_k": self.top_k,
            "model": self.llm_client.model_name,
            "ollama_available": self.llm_client.check_availability(),
            "documents": self.vector_db.get_all_documents(),
            "pipeline_type": "structure_aware"
        }
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of all uploaded documents"""
        return self.vector_db.get_all_documents()
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """Delete a specific document"""
        try:
            success = self.vector_db.delete_document(filename)
            if success:
                return {
                    "status": "success",
                    "message": f"Document '{filename}' deleted successfully",
                    "vector_db_count": self.vector_db.get_collection_count()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Document '{filename}' not found"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def clear_all_documents(self) -> Dict[str, Any]:
        """Clear all documents"""
        try:
            self.vector_db.reset_collection()
            return {
                "status": "success",
                "message": "All documents cleared successfully",
                "vector_db_count": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
