"""
Pydantic Request/Response Models
Type-safe API schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class Message(BaseModel):
    """Single message in conversation"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request schema with conversational support"""
    question: str = Field(..., description="User question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    chat_history: Optional[List[Message]] = Field(None, description="Recent chat history")
    top_k: Optional[int] = Field(5, description="Number of documents to retrieve")
    debug: Optional[bool] = Field(False, description="Include debug information in response")


class RAGResponse(BaseModel):
    """Structured V1 answer payload with citations and confidence."""
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0


class ChatResponse(BaseModel):
    """Chat response schema with conversational support"""
    answer: str
    session_id: Optional[str] = None
    citations: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    processing_time: str
    metadata: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0


class UploadResponse(BaseModel):
    """PDF upload response schema"""
    status: str
    filename: str
    total_pages: int
    total_chunks: int
    vector_db_count: int
    processing_time: str
    upload_timestamp: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information schema"""
    filename: str
    chunk_count: int
    upload_timestamp: str


class StatusResponse(BaseModel):
    """Pipeline status response"""
    vector_db_count: int
    chunk_size: int
    chunk_overlap: int
    top_k: int
    model: str
    ollama_available: bool
    documents: List[DocumentInfo] = []
