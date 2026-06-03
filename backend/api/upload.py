"""
PDF Upload API Endpoint
Handles PDF file upload and ingestion
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from services.rag_pipeline import RAGPipeline
from schemas.request_models import UploadResponse

router = APIRouter()

# Initialize RAG Pipeline (singleton pattern)
rag_pipeline = RAGPipeline()

# Upload directory
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process PDF document with incremental ingestion
    Supports multiple document uploads without overwriting existing data
    
    Pipeline:
    1. Validate PDF file
    2. Save to disk
    3. Load and parse PDF
    4. Chunk text
    5. Generate embeddings
    6. Append to vector database (incremental)
    
    Returns:
        Upload status with ingestion metrics
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        from datetime import datetime
        
        # Save uploaded file with timestamp to avoid overwrites
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            # Check if already in database
            existing_docs = rag_pipeline.get_documents()
            if any(doc["filename"] == safe_filename for doc in existing_docs):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Document '{safe_filename}' already uploaded. Please delete it first or rename the file."
                )
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Saved file: {file_path}")
        
        # Process PDF through RAG pipeline (incremental ingestion)
        upload_timestamp = datetime.now().isoformat()
        result = rag_pipeline.ingest_pdf(file_path, upload_timestamp)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    finally:
        await file.close()


@router.get("/status")
async def get_status():
    """Get current RAG pipeline status"""
    try:
        status = rag_pipeline.get_status()
        return JSONResponse(content=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/documents")
async def get_documents():
    """Get list of all uploaded documents"""
    try:
        documents = rag_pipeline.get_documents()
        return JSONResponse(content={"documents": documents})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document"""
    try:
        result = rag_pipeline.delete_document(filename)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def clear_all_documents():
    """Clear all documents from the database"""
    try:
        result = rag_pipeline.clear_all_documents()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
