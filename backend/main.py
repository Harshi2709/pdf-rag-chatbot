"""
FastAPI Main Application Entry Point
Production-level PDF RAG Chat Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.upload import router as upload_router
from api.chat import router as chat_router

app = FastAPI(
    title="PDF RAG Chat API",
    description="Production-level Retrieval-Augmented Generation API for PDF Question Answering",
    version="1.0.0"
)

# CORS Configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])


@app.get("/health")
async def health_check():
    """Backend health check endpoint"""
    return {
        "status": "healthy",
        "service": "PDF RAG Chat API",
        "version": "1.0.0"
    }


@app.get("/status")
async def status():
    """Backend status endpoint for frontend connectivity check"""
    return {
        "status": "running",
        "message": "Backend is operational",
        "service": "PDF RAG Chat API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PDF RAG Chat API",
        "docs": "/docs",
        "health": "/health",
        "status": "/status"
    }
