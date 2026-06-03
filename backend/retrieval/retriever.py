"""
Retrieval Module
Implements explicit semantic retrieval without abstractions
"""
from typing import List, Dict, Optional, Any
from embeddings.embedding_model import embedding_model
from vectordb.chroma_client import ChromaDBClient


class RetrievedDocument:
    """Represents a retrieved document with metadata and similarity score"""
    
    def __init__(self, text: str, metadata: Dict[str, Any], similarity_score: float):
        self.text = text
        self.metadata = metadata
        self.similarity_score = similarity_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score
        }


class Retriever:
    """
    Explicit Retrieval Implementation
    Manually handles query embedding, similarity search, and context assembly
    """
    
    def __init__(self, vector_db: ChromaDBClient, top_k: int = 5):
        """
        Initialize retriever
        
        Args:
            vector_db: ChromaDB client instance
            top_k: Number of top documents to retrieve
        """
        self.vector_db = vector_db
        self.top_k = top_k
        self.embedding_model = embedding_model
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query string
            top_k: Override default top_k value
        
        Returns:
            List of RetrievedDocument objects
        """
        k = top_k if top_k is not None else self.top_k
        
        # Step 1: Convert query to embedding
        print(f"Generating embedding for query: {query[:50]}...")
        query_embedding = self.embedding_model.embed_text(query)
        
        # Step 2: Perform similarity search
        print(f"Performing similarity search (top_k={k})...")
        search_results = self.vector_db.similarity_search(
            query_embedding=query_embedding,
            top_k=k
        )
        
        # Step 3: Assemble retrieved documents
        retrieved_docs = []
        
        for i, (text, metadata, distance) in enumerate(zip(
            search_results["documents"],
            search_results["metadatas"],
            search_results["distances"]
        )):
            # Convert distance to similarity score (lower distance = higher similarity)
            similarity_score = 1.0 / (1.0 + distance)
            
            doc = RetrievedDocument(
                text=text,
                metadata=metadata,
                similarity_score=similarity_score
            )
            retrieved_docs.append(doc)
        
        print(f"Retrieved {len(retrieved_docs)} documents")
        return retrieved_docs
    
    def assemble_context(self, retrieved_docs: List[RetrievedDocument]) -> str:
        """
        Manually assemble context from retrieved documents
        Shows actual document names and groups chunks by document
        
        Args:
            retrieved_docs: List of retrieved documents
        
        Returns:
            Assembled context string with clear document identification
        """
        if not retrieved_docs:
            return ""
        
        # Group chunks by document for better organization
        doc_groups = {}
        for doc in retrieved_docs:
            filename = doc.metadata.get("filename", "unknown")
            if filename not in doc_groups:
                doc_groups[filename] = []
            doc_groups[filename].append(doc)
        
        context_parts = []
        
        # Add summary header
        doc_summary = ", ".join([f"{name} ({len(chunks)} chunks)" 
                                for name, chunks in doc_groups.items()])
        context_parts.append(f"Retrieved from: {doc_summary}\n")
        
        # Add each chunk with clear source identification
        chunk_num = 1
        for filename, docs in doc_groups.items():
            for doc in docs:
                page = doc.metadata.get("page", "unknown")
                similarity = f" (relevance: {doc.similarity_score:.2f})" if hasattr(doc, 'similarity_score') else ""
                
                context_part = f"[Chunk {chunk_num} - {filename}, Page {page}{similarity}]\n{doc.text}\n"
                context_parts.append(context_part)
                chunk_num += 1
        
        return "\n".join(context_parts)
    
    def extract_citations(self, retrieved_docs: List[RetrievedDocument]) -> List[Dict[str, Any]]:
        """
        Extract source citations from retrieved documents
        
        Args:
            retrieved_docs: List of retrieved documents
        
        Returns:
            List of citation dictionaries
        """
        citations = []
        seen = set()
        
        for doc in retrieved_docs:
            filename = doc.metadata.get("filename", "unknown")
            page = doc.metadata.get("page", "unknown")
            
            citation_key = f"{filename}_{page}"
            
            if citation_key not in seen:
                citations.append({
                    "file": filename,
                    "page": page
                })
                seen.add(citation_key)
        
        return citations
