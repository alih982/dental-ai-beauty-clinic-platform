from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
from app.infrastructure.database import get_db
from app.services.rag_service import rag_service
from pydantic import BaseModel

router = APIRouter(prefix="/rag", tags=["RAG System"])

class QueryRequest(BaseModel):
    question: str

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process a PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save temp file
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        result = await rag_service.ingest_document(db, temp_path, {"filename": file.filename})
        return {"success": True, "message": "Document ingested successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/query")
async def query_rag(request: QueryRequest, db: Session = Depends(get_db)):
    """Search and generate response from ingested documents"""
    try:
        result = await rag_service.query(db, request.question)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
