"""
Chat API Endpoint
Handles conversational question answering with RAG
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from schemas.request_models import ChatRequest, ChatResponse
from services.conversational_rag import ConversationalRAG
from vectordb.chroma_client import ChromaDBClient

router = APIRouter()

# Initialize Conversational RAG (singleton pattern)
vector_db = ChromaDBClient()
conversational_rag = ConversationalRAG(vector_db=vector_db, top_k=5)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Answer question using Conversational RAG pipeline
    
    Conversational Pipeline:
    1. Conversation Memory → Retrieve session history
    2. Intent Classification → Determine query type
    3. Query Rewriting → Convert to standalone query
    4. Retrieval Decision → Decide if retrieval needed
    5. Document Retrieval → Get relevant chunks (if needed)
    6. Prompt Construction → Build context-aware prompt
    7. LLM Response → Generate answer
    8. Memory Update → Store interaction
    
    Args:
        request: ChatRequest with question, optional session_id, chat_history, and debug flag
    
    Returns:
        ChatResponse with answer, session_id, citations, and optional debug info
    """
    if not request.question or request.question.strip() == "":
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Convert Pydantic Message models to dictionaries
        chat_history = None
        if request.chat_history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chat_history
            ]
        
        # Process query through Conversational RAG pipeline
        result = conversational_rag.chat(
            query=request.question,
            session_id=request.session_id,
            chat_history=chat_history,
            debug=request.debug or False
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get information about a conversation session
    
    Args:
        session_id: Session ID to query
    
    Returns:
        Session information
    """
    try:
        result = conversational_rag.get_session_info(session_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session ID to clear
    
    Returns:
        Success message
    """
    try:
        result = conversational_rag.clear_session(session_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")
