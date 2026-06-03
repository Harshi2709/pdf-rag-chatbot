"""
ChromaDB Vector Database Client
Handles vector storage and similarity search with multi-document support
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import os
from datetime import datetime


class ChromaDBClient:
    """
    ChromaDB Client for vector storage and retrieval
    Implements persistent storage with semantic similarity search
    Supports multi-document incremental ingestion
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client with persistent storage
        
        Args:
            persist_directory: Directory for persistent vector storage
        """
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Collection name for PDF documents
        self.collection_name = "pdf_documents"
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Multi-document PDF chunks with embeddings"}
        )
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add documents to vector database
        
        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        """
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(texts)} documents to ChromaDB")
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_filenames: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform similarity search using query embedding
        Supports filtering by document filenames
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            filter_filenames: Optional list of filenames to filter results
        
        Returns:
            Dictionary containing documents, metadatas, and distances
        """
        where_filter = None
        if filter_filenames:
            # Create filter for specific documents
            where_filter = {"filename": {"$in": filter_filenames}}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    
    def get_collection_count(self) -> int:
        """Get total number of documents in collection"""
        return self.collection.count()
    
    def delete_collection(self) -> None:
        """Delete the entire collection"""
        self.client.delete_collection(name=self.collection_name)
        print(f"Deleted collection: {self.collection_name}")
    
    def reset_collection(self) -> None:
        """Reset collection by deleting and recreating"""
        try:
            self.client.delete_collection(name=self.collection_name)
        except:
            pass
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Multi-document PDF chunks with embeddings"}
        )
        print("Collection reset successfully")
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get list of all unique documents in the collection
        
        Returns:
            List of document metadata dictionaries
        """
        try:
            # Get all items from collection
            results = self.collection.get()
            
            if not results or not results.get("metadatas"):
                return []
            
            # Extract unique documents
            documents = {}
            for metadata in results["metadatas"]:
                filename = metadata.get("filename", "unknown")
                if filename not in documents:
                    documents[filename] = {
                        "filename": filename,
                        "chunk_count": 0,
                        "upload_timestamp": metadata.get("upload_timestamp", "unknown")
                    }
                documents[filename]["chunk_count"] += 1
            
            return list(documents.values())
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
    
    def delete_document(self, filename: str) -> bool:
        """
        Delete all chunks for a specific document
        
        Args:
            filename: Name of the document to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"filename": filename}
            )
            
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
                print(f"Deleted {len(results['ids'])} chunks for {filename}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
