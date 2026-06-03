"""
RAG Pipeline Service
Orchestrates the complete RAG workflow
"""
import time
from typing import Dict, List, Any
from loaders.pdf_loader import PDFLoader
from chunking.splitter import RecursiveCharacterTextSplitter
from embeddings.embedding_model import embedding_model
from vectordb.chroma_client import ChromaDBClient
from retrieval.retriever import Retriever
from llm.ollama_client import OllamaClient
from prompts.rag_prompt import RAGPromptTemplate


class RAGPipeline:
    """
    Complete RAG Pipeline Implementation
    Explicitly implements each stage of the RAG workflow
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        top_k: int = 5,
        model_name: str = "llama3"
    ):
        """
        Initialize RAG Pipeline
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            top_k: Number of documents to retrieve
            model_name: Ollama model name
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        
        # Initialize components
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedding_model = embedding_model
        self.vector_db = ChromaDBClient()
        self.retriever = Retriever(vector_db=self.vector_db, top_k=top_k)
        self.llm_client = OllamaClient(model_name=model_name)
        self.prompt_template = RAGPromptTemplate()
    
    def ingest_pdf(self, file_path: str, upload_timestamp: str = None) -> Dict[str, Any]:
        """
        Complete PDF ingestion pipeline with incremental support
        Appends to existing vector database without overwriting
        
        Pipeline stages:
        1. PDF Loading
        2. Text Chunking
        3. Embedding Generation
        4. Incremental Vector Storage
        
        Args:
            file_path: Path to PDF file
            upload_timestamp: Timestamp of upload (for tracking)
        
        Returns:
            Ingestion status dictionary
        """
        start_time = time.time()
        
        try:
            # Stage 1: PDF Loading
            print("Stage 1: Loading PDF...")
            loader = PDFLoader(file_path)
            pdf_document = loader.load()
            print(f"Loaded {pdf_document.total_pages} pages from {pdf_document.filename}")
            
            # Stage 2: Text Chunking
            print("Stage 2: Chunking text...")
            chunks = self.text_splitter.create_chunks(pdf_document.pages)
            print(f"Created {len(chunks)} chunks")
            
            # Stage 3: Embedding Generation
            print("Stage 3: Generating embeddings...")
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_model.embed_texts(texts)
            print(f"Generated {len(embeddings)} embeddings")
            
            # Stage 4: Incremental Vector Storage
            print("Stage 4: Appending to vector database...")
            
            # Add upload timestamp to metadata
            if upload_timestamp is None:
                from datetime import datetime
                upload_timestamp = datetime.now().isoformat()
            
            metadatas = [chunk.metadata for chunk in chunks]
            for metadata in metadatas:
                metadata["upload_timestamp"] = upload_timestamp
            
            ids = [chunk.chunk_id for chunk in chunks]
            
            # Append to existing collection (incremental ingestion)
            self.vector_db.add_documents(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "filename": pdf_document.filename,
                "total_pages": pdf_document.total_pages,
                "total_chunks": len(chunks),
                "vector_db_count": self.vector_db.get_collection_count(),
                "processing_time": f"{processing_time:.2f}s",
                "upload_timestamp": upload_timestamp
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processing_time": f"{time.time() - start_time:.2f}s"
            }
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Complete RAG query pipeline
        
        Pipeline stages:
        1. Query Embedding
        2. Similarity Search
        3. Top-K Retrieval
        4. Context Assembly
        5. Prompt Construction
        6. LLM Inference
        7. Response Generation
        
        Args:
            question: User question
        
        Returns:
            Response dictionary with answer, citations, and debug info
        """
        start_time = time.time()
        
        try:
            # Stage 1-3: Retrieval
            print("Stages 1-3: Retrieving relevant documents...")
            retrieved_docs = self.retriever.retrieve(question, top_k=self.top_k)
            
            # Stage 4: Context Assembly
            print("Stage 4: Assembling context...")
            context = self.retriever.assemble_context(retrieved_docs)
            
            # Stage 5: Prompt Construction
            print("Stage 5: Building prompt...")
            prompt = self.prompt_template.build_prompt(context, question)
            
            # Stage 6-7: LLM Inference
            print("Stages 6-7: Generating response...")
            answer = self.llm_client.generate(prompt, temperature=0.7)
            
            # Extract citations
            citations = self.retriever.extract_citations(retrieved_docs)
            
            processing_time = time.time() - start_time
            
            return {
                "answer": answer.strip(),
                "citations": citations,
                "retrieved_chunks": [doc.to_dict() for doc in retrieved_docs],
                "processing_time": f"{processing_time:.2f}s",
                "metadata": {
                    "num_chunks_retrieved": len(retrieved_docs),
                    "model": self.llm_client.model_name
                }
            }
        
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "retrieved_chunks": [],
                "processing_time": f"{time.time() - start_time:.2f}s",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status with document list"""
        return {
            "vector_db_count": self.vector_db.get_collection_count(),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "model": self.llm_client.model_name,
            "ollama_available": self.llm_client.check_availability(),
            "documents": self.vector_db.get_all_documents()
        }
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of all uploaded documents"""
        return self.vector_db.get_all_documents()
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a specific document from the vector database
        
        Args:
            filename: Name of the document to delete
        
        Returns:
            Status dictionary
        """
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
        """Clear all documents from the vector database"""
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
