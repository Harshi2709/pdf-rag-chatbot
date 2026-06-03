"""
Reranking Module
Improves retrieval quality using cross-encoder models
"""
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
import numpy as np


class Reranker:
    """
    Cross-Encoder Reranker for improving retrieval quality
    Uses a more sophisticated model to score query-document pairs
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(Reranker, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker model (only once due to singleton)
        
        Args:
            model_name: Name of the cross-encoder model
                       Default: cross-encoder/ms-marco-MiniLM-L-6-v2
                       - Fast and accurate
                       - Trained on MS MARCO dataset
                       - Good for general Q&A
        
        Alternative models:
            - "cross-encoder/ms-marco-MiniLM-L-12-v2" (more accurate, slower)
            - "BAAI/bge-reranker-base" (multilingual support)
        """
        if self._model is None:
            print(f"Loading reranker model: {model_name}")
            self._model = CrossEncoder(model_name)
            self.model_name = model_name
            print(f"Reranker model loaded successfully")
    
    def rerank(
        self, 
        query: str, 
        documents: List[str],
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to query
        
        Args:
            query: User query
            documents: List of document texts to rerank
            top_k: Number of top documents to return
            return_scores: Whether to include relevance scores
        
        Returns:
            List of dictionaries with 'index' and 'score' (if return_scores=True)
            Sorted by relevance (highest first)
        
        Example:
            query = "What caused the revenue decline?"
            docs = ["Revenue was $2M", "Market crash led to losses", ...]
            results = reranker.rerank(query, docs, top_k=3)
            # [{'index': 1, 'score': 0.95}, {'index': 0, 'score': 0.78}, ...]
        """
        if not documents:
            return []
        
        # Create query-document pairs for cross-encoder
        pairs = [[query, doc] for doc in documents]
        
        # Get relevance scores (cross-encoder evaluates each pair together)
        scores = self._model.predict(pairs)
        
        # Sort by score (highest first)
        scored_docs = [
            {'index': idx, 'score': float(score)}
            for idx, score in enumerate(scores)
        ]
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top-k
        results = scored_docs[:top_k]
        
        if not return_scores:
            return [{'index': item['index']} for item in results]
        
        return results
    
    def rerank_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        text_field: str = 'text',
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents that have metadata attached
        
        Args:
            query: User query
            documents: List of document dicts with text and metadata
            text_field: Field name containing document text
            top_k: Number of top documents to return
        
        Returns:
            Reranked documents with original metadata + rerank_score
        
        Example:
            docs = [
                {'text': 'Revenue was $2M', 'page': 3, 'filename': 'report.pdf'},
                {'text': 'Market crash...', 'page': 7, 'filename': 'notes.pdf'}
            ]
            results = reranker.rerank_with_metadata(query, docs, top_k=1)
            # Returns docs with highest relevance, preserving all metadata
        """
        if not documents:
            return []
        
        # Extract texts for reranking
        texts = [doc.get(text_field, '') for doc in documents]
        
        # Get reranked indices with scores
        reranked = self.rerank(query, texts, top_k=top_k, return_scores=True)
        
        # Map back to original documents with scores
        results = []
        for item in reranked:
            idx = item['index']
            doc = documents[idx].copy()
            doc['rerank_score'] = item['score']
            results.append(doc)
        
        return results
    
    def get_relevance_threshold(self) -> float:
        """
        Get recommended relevance threshold for filtering
        
        Returns:
            Threshold value (documents below this are likely irrelevant)
        
        Typical thresholds:
            - > 0.7: Highly relevant
            - 0.3-0.7: Moderately relevant
            - < 0.3: Likely irrelevant
        """
        return 0.3


# Global singleton instance
reranker = Reranker()
