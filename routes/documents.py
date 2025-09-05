from fastapi import APIRouter, HTTPException, UploadFile, File
from models import DocumentUpload, HealthResponse
from services.pinecone_service import PineconeService
from typing import Dict, List, Any
import json

router = APIRouter(prefix="/documents", tags=["documents"])
pinecone_service = PineconeService()

@router.post("/upload")
async def upload_document(document: DocumentUpload) -> Dict[str, str]:
    try:
        doc_id = pinecone_service.store_document(
            content=document.content, title=document.title, metadata=document.metadata
        )

        return {"message": "Document uploaded successfully", "document_id": doc_id}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error uploading document: {str(e)}"
        )

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...), title: str = None
) -> Dict[str, str]:
    try:
        content = await file.read()
        text_content = content.decode("utf-8")

        document_title = title or file.filename or "Untitled Document"

        doc_id = pinecone_service.store_document(
            content=text_content,
            title=document_title,
            metadata={"filename": file.filename, "content_type": file.content_type},
        )

        return {
            "message": "File uploaded successfully",
            "document_id": doc_id,
            "filename": file.filename,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/search")
async def search_documents(query: str, top_k: int = 5) -> Dict[str, Any]:
    try:
        documents = pinecone_service.search_similar_documents(query, top_k)

        return {"query": query, "results": documents, "count": len(documents)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching documents: {str(e)}"
        )

@router.delete("/{document_id}")
async def delete_document(document_id: str) -> Dict[str, str]:
    try:
        success = pinecone_service.delete_document(document_id)

        if success:
            return {"message": "Document deleted successfully"}
        else:
            return {"message": "Failed to delete document"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting document: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", message="Documents service is running")
