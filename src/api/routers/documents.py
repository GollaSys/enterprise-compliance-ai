from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional
import structlog
from src.services.document_service import DocumentService

router = APIRouter()
logger = structlog.get_logger()
doc_service = DocumentService()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "general"
):
    try:
        if file.size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=413, detail="File too large")

        content = await file.read()
        result = await doc_service.upload_document(
            file_content=content,
            filename=file.filename,
            doc_type=doc_type,
            metadata={"content_type": file.content_type}
        )

        return {
            "message": "Document uploaded successfully",
            "document": result
        }
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_documents(
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    try:
        documents = await doc_service.list_documents(doc_type, status, limit, offset)
        return {
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Document listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    try:
        document = await doc_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    try:
        success = await doc_service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Document deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))