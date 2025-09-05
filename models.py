from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[str]] = []

class DocumentUpload(BaseModel):
    content: str
    title: str
    metadata: Optional[dict] = {}

class HealthResponse(BaseModel):
    status: str
    message: str
