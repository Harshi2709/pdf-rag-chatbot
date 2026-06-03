"""
RAG Prompt Engineering Module
Custom prompt templates for retrieval-augmented generation
"""
from typing import List


class RAGPromptTemplate:
    """
    Custom RAG Prompt Template
    Ensures model answers strictly from context and refuses unsupported queries
    """
    
    SYSTEM_INSTRUCTION = """You are a helpful AI assistant that answers questions based STRICTLY on the provided document context.

CRITICAL RULES:
1. Answer ONLY using information from the provided context
2. If the context does not contain enough information to answer the question, respond with: "The uploaded document does not contain enough information to answer this question."
3. Do NOT use external knowledge or make assumptions
4. Do NOT hallucinate or fabricate information
5. Cite the source (filename and page number) when possible
6. Be concise and accurate
7. If the question is unclear, ask for clarification

Your goal is to provide accurate, context-based answers while maintaining transparency about the limitations of the available information."""
    
    @staticmethod
    def build_prompt(context: str, question: str) -> str:
        """
        Build complete RAG prompt with instructions, context, and question
        
        Args:
            context: Retrieved document context
            question: User question
        
        Returns:
            Complete formatted prompt
        """
        if not context or context.strip() == "":
            return f"""{RAGPromptTemplate.SYSTEM_INSTRUCTION}

CONTEXT:
No relevant context found in the uploaded documents.

QUESTION:
{question}

ANSWER:
The uploaded document does not contain enough information to answer this question."""
        
        prompt = f"""{RAGPromptTemplate.SYSTEM_INSTRUCTION}

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""
        
        return prompt
    
    @staticmethod
    def build_chat_messages(context: str, question: str) -> List[dict]:
        """
        Build chat messages format for Ollama chat API
        
        Args:
            context: Retrieved document context
            question: User question
        
        Returns:
            List of message dictionaries
        """
        system_message = {
            "role": "system",
            "content": RAGPromptTemplate.SYSTEM_INSTRUCTION
        }
        
        user_message = {
            "role": "user",
            "content": f"""CONTEXT:
{context}

QUESTION:
{question}"""
        }
        
        return [system_message, user_message]
