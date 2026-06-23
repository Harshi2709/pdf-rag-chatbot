"""Answer quality evaluation helpers for V1."""
from typing import Dict


class AnswerMetrics:
    """Simple semantic similarity and faithfulness proxies for V1."""

    def semantic_similarity(self, answer: str, reference: str) -> float:
        if not answer or not reference:
            return 0.0
        common = set(answer.lower().split()) & set(reference.lower().split())
        return round(len(common) / max(1, len(set(reference.lower().split()))), 2)

    def evaluate(self, answer: str, reference: str) -> Dict[str, float]:
        return {
            "semantic_similarity": self.semantic_similarity(answer, reference),
            "answer_relevance": 0.8 if answer and reference and set(reference.lower().split()) & set(answer.lower().split()) else 0.5,
        }
