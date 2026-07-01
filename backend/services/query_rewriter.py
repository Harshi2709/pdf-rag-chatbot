"""
Query Rewriting Module
Converts conversational queries into standalone searchable queries
"""
from typing import List, Dict, Any, Optional
from llm.ollama_client import OllamaClient
from utils.logging_config import get_logger

logger = get_logger(__name__)


class QueryRewriter:
    """
    Rewrites vague conversational queries into explicit standalone queries
    Critical for improving retrieval quality in conversational RAG
    """
    
    REWRITING_PROMPT = """You are a query rewriting assistant for a document Q&A system.

Your task: Convert conversational, context-dependent queries into standalone, explicit search queries.

RULES:
1. Resolve ALL references (that, this, it, they, previous, etc.)
2. Resolve ALL pronouns with specific entities
3. Include relevant context from conversation history
4. Make the query completely self-contained
5. Keep the user's intent intact
6. Output ONLY the rewritten query (no explanation)

EXAMPLES:

Example 1:
History: User: "What does the document say about AI replacing developers?"
Query: "Can you summarize that?"
Rewritten: "Summarize what the document says about AI replacing developers"

Example 2:
History: User: "What are the main findings in the research paper?"
Query: "What about the methodology?"
Rewritten: "What methodology was used in the research paper mentioned previously?"

Example 3:
History: 
  User: "What's the company's Q3 revenue?"
  Assistant: "Q3 revenue was $4.2M, up 23% from Q2."
Query: "How does that compare to Q1?"
Rewritten: "How does the Q3 revenue of $4.2M compare to Q1 revenue?"

Example 4:
History: User: "Tell me about the climate report findings"
Query: "What did the second section say?"
Rewritten: "What did the second section of the climate report say about the findings?"

Example 5:
History: 
  User: "What are the benefits of remote work?"
  Assistant: "The document mentions increased productivity, cost savings, and better work-life balance."
Query: "Any drawbacks mentioned?"
Rewritten: "What drawbacks of remote work are mentioned in the document?"

NOW REWRITE THIS QUERY:

CONVERSATION HISTORY:
{history}

CURRENT QUERY:
{query}

REWRITTEN QUERY:"""
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize query rewriter
        
        Args:
            llm_client: LLM client for rewriting (uses Ollama by default)
        """
        self.llm_client = llm_client or OllamaClient()
    
    def rewrite(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]] = None,
        intent: str = "document_qa"
    ) -> Dict[str, Any]:
        """
        Rewrite conversational query into standalone query
        
        Args:
            query: Original user query
            conversation_history: Recent conversation messages
            intent: Detected intent (helps with rewriting strategy)
        
        Returns:
            Dictionary with original and rewritten queries
        """
        # Check if rewriting is needed
        if not self._needs_rewriting(query, conversation_history):
            return {
                "original_query": query,
                "rewritten_query": query,
                "was_rewritten": False,
                "reason": "Query is already standalone"
            }
        
        # Format conversation history
        history_str = self._format_history(conversation_history or [])
        
        # Build rewriting prompt
        prompt = self.REWRITING_PROMPT.format(
            history=history_str,
            query=query
        )
        
        try:
            # Get rewritten query from LLM
            rewritten = self.llm_client.generate(prompt, temperature=0.3)
            rewritten = rewritten.strip()
            
            # Clean up the response
            rewritten = self._clean_rewritten_query(rewritten)
            
            return {
                "original_query": query,
                "rewritten_query": rewritten,
                "was_rewritten": True,
                "reason": "Resolved references and context"
            }
        
        except Exception as e:
            logger.exception("Query rewriting error")
            # Fallback to rule-based rewriting
            return self._fallback_rewrite(query, conversation_history)
    
    def _needs_rewriting(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> bool:
        """
        Determine if query needs rewriting
        
        Args:
            query: User query
            conversation_history: Recent messages
        
        Returns:
            Boolean indicating if rewriting is needed
        """
        # No history = no context to resolve
        if not conversation_history or len(conversation_history) == 0:
            return False
        
        query_lower = query.lower()
        
        # Reference words that indicate context dependence
        reference_patterns = [
            "that", "this", "it", "they", "them", "those", "these",
            "previous", "earlier", "above", "before",
            "first", "second", "third", "last",
            "same", "other", "another"
        ]
        
        # Check for references
        has_reference = any(pattern in query_lower.split() for pattern in reference_patterns)
        
        # Check for pronouns
        pronouns = ["he", "she", "his", "her", "its"]
        has_pronoun = any(p in query_lower.split() for p in pronouns)
        
        # Check for short vague queries
        is_vague = len(query.split()) < 6 and any(
            word in query_lower for word in ["what", "how", "why", "explain"]
        )
        
        return has_reference or has_pronoun or is_vague
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        # Use last 4 messages for context (2 exchanges)
        for msg in history[-4:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content[:200]}")  # Limit length
        
        return "\n".join(formatted)
    
    def _clean_rewritten_query(self, rewritten: str) -> str:
        """
        Clean up LLM-generated rewritten query
        
        Args:
            rewritten: Raw rewritten query from LLM
        
        Returns:
            Cleaned query
        """
        # Remove common prefixes the LLM might add
        prefixes = [
            "rewritten query:",
            "rewritten:",
            "query:",
            "standalone query:",
            "search query:"
        ]
        
        rewritten_lower = rewritten.lower()
        for prefix in prefixes:
            if rewritten_lower.startswith(prefix):
                rewritten = rewritten[len(prefix):].strip()
        
        # Remove quotes if the whole thing is quoted
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
        
        if rewritten.startswith("'") and rewritten.endswith("'"):
            rewritten = rewritten[1:-1]
        
        return rewritten.strip()
    
    def _fallback_rewrite(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Rule-based fallback rewriting
        Used if LLM rewriting fails
        """
        if not conversation_history:
            return {
                "original_query": query,
                "rewritten_query": query,
                "was_rewritten": False,
                "reason": "No conversation history"
            }
        
        # Get last user message for context
        last_user_msg = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        # Simple concatenation fallback
        if last_user_msg:
            rewritten = f"{query} (context: {last_user_msg[:100]})"
            return {
                "original_query": query,
                "rewritten_query": rewritten,
                "was_rewritten": True,
                "reason": "Rule-based context injection"
            }
        
        return {
            "original_query": query,
            "rewritten_query": query,
            "was_rewritten": False,
            "reason": "Fallback - no rewriting possible"
        }
