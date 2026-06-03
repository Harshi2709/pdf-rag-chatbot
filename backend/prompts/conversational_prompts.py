"""
Conversational RAG Prompt Templates
Includes conversation history context
"""


class ConversationalRAGPrompt:
    """
    Prompt template for conversational RAG with history awareness
    """
    
    SYSTEM_INSTRUCTIONS = """You are an AI assistant specialized in answering questions based on uploaded PDF documents.

Your capabilities:
- Answer questions using retrieved document content
- Maintain conversational continuity across multiple turns
- Reference previous conversation when relevant
- Acknowledge when information is not in the documents
- Provide clear, accurate, and contextual responses

CRITICAL RULES:
1. ALWAYS prioritize retrieved document content when answering factual questions
2. Reference conversation history when answering follow-up questions
3. If the answer is NOT in the retrieved context, clearly state: "I don't find that information in the documents."
4. Do NOT make up information or hallucinate facts
5. Include citations with document names and page numbers when possible
6. Maintain a helpful, conversational tone
7. Handle references like "that", "this", "it" by referring to previous context
8. For summarization requests, synthesize information from retrieved content
9. For comparison requests, analyze retrieved content from multiple sources

FORMAT:
- Provide direct, clear answers
- Use natural conversational language
- Include citations in format: [DocumentName, Page X]
- Reference previous conversation naturally when relevant"""
    
    CONVERSATIONAL_TEMPLATE = """SYSTEM INSTRUCTIONS:
{system_instructions}

CONVERSATION HISTORY:
{conversation_history}

RETRIEVED DOCUMENT CONTEXT:
{retrieved_context}

CURRENT QUESTION:
{current_question}

ASSISTANT RESPONSE:"""
    
    NO_RETRIEVAL_TEMPLATE = """SYSTEM INSTRUCTIONS:
You are a helpful AI assistant in a document Q&A system.

CONVERSATION HISTORY:
{conversation_history}

CURRENT QUESTION:
{current_question}

NOTE: This question does not require document retrieval. Respond conversationally based on the conversation history.

ASSISTANT RESPONSE:"""
    
    def build_conversational_prompt(
        self,
        question: str,
        retrieved_context: str,
        conversation_history: str,
        use_retrieval: bool = True
    ) -> str:
        """
        Build prompt for conversational RAG
        
        Args:
            question: Current user question
            retrieved_context: Retrieved document chunks
            conversation_history: Formatted conversation history
            use_retrieval: Whether to include retrieved context
        
        Returns:
            Formatted prompt string
        """
        if use_retrieval:
            return self.CONVERSATIONAL_TEMPLATE.format(
                system_instructions=self.SYSTEM_INSTRUCTIONS,
                conversation_history=conversation_history,
                retrieved_context=retrieved_context,
                current_question=question
            )
        else:
            return self.NO_RETRIEVAL_TEMPLATE.format(
                conversation_history=conversation_history,
                current_question=question
            )
    
    def build_simple_prompt(
        self,
        question: str,
        conversation_history: str
    ) -> str:
        """
        Build simple conversational prompt without retrieval
        Used for greetings, meta questions, feedback, etc.
        
        Args:
            question: Current user question
            conversation_history: Formatted conversation history
        
        Returns:
            Formatted prompt string
        """
        return self.NO_RETRIEVAL_TEMPLATE.format(
            conversation_history=conversation_history,
            current_question=question
        )
