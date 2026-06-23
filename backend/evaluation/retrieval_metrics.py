"""Basic retrieval metrics for V1 evaluation."""
from typing import List, Dict


class RetrievalMetrics:
    """Compute simple Recall@K and Precision@K approximations."""

    def recall_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        top_k = retrieved[:k]
        hits = len(set(top_k) & set(relevant))
        return round(hits / max(1, len(relevant)), 2)

    def precision_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        top_k = retrieved[:k]
        hits = len(set(top_k) & set(relevant))
        return round(hits / max(1, len(top_k)), 2)

    def report(self, retrieved: List[str], relevant: List[str], k: int) -> Dict[str, float]:
        return {
            "recall_at_k": self.recall_at_k(retrieved, relevant, k),
            "precision_at_k": self.precision_at_k(retrieved, relevant, k),
        }
