"""
Embedding Model Module
Handles text embedding generation using sentence-transformers
Implements singleton pattern for model reuse
"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from utils.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """
    Singleton Embedding Model
    Uses BAAI/bge-base-en-v1.5 for local embedding generation with fallback support.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        """
        Initialize embedding model (only once due to singleton)
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        if self._model is None:
            logger.info(f"Loading embedding model: {model_name}")
            try:
                self._model = SentenceTransformer(model_name)
            except Exception:
                fallback_model = "all-MiniLM-L6-v2"
                logger.warning(f"Primary model unavailable, falling back to {fallback_model}")
                self._model = SentenceTransformer(fallback_model)
                model_name = fallback_model
            self.model_name = model_name
            self.embedding_dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dimension}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.embedding_dimension


# Global singleton instance
embedding_model = EmbeddingModel()
