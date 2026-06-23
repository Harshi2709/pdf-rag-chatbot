"""Simple RAGAS-style evaluation helpers for V1."""
from typing import Dict, Any


class RAGASEvaluator:
    """Minimal evaluator placeholder that reports quality dimensions."""

    def evaluate(self, answer: str, context: str, question: str) -> Dict[str, Any]:
        context_coverage = 1.0 if context and question.lower() in context.lower() else 0.6
        faithfulness = 0.85 if answer and context else 0.0
        answer_relevance = 0.8 if answer and question.lower() in answer.lower() else 0.6
        return {
            "faithfulness": round(faithfulness, 2),
            "answer_relevance": round(answer_relevance, 2),
            "context_precision": round(context_coverage, 2),
            "context_recall": round(context_coverage, 2),
        }
