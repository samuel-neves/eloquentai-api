from fastapi import APIRouter, HTTPException, Depends
from models import ChatRequest, ChatResponse, HealthResponse
from services.chat_service import ChatService
from services.auth_service import AuthService
from routes.auth import get_session_from_header
from typing import Dict, Any, Optional

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()
auth_service = AuthService()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    session: Optional[Dict[str, Any]] = Depends(get_session_from_header),
) -> ChatResponse:
    try:
        if not chat_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Chat service is not properly configured. Please check your API keys.",
            )

        if not session:
            session_id = auth_service.create_session()
            session = auth_service.get_session(session_id)
        else:
            session_id = session["session_id"]

        conversation_id = request.conversation_id or session_id

        result = chat_service.generate_response(
            message=request.message, conversation_id=conversation_id
        )

        auth_service.update_session_activity(
            session_id, {"new_conversation": conversation_id != session_id}
        )

        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            sources=result["sources"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        )

@router.get("/conversation/{conversation_id}")
async def get_conversation_history(conversation_id: str) -> Dict[str, Any]:
    try:
        history = chat_service.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "messages": history}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving conversation: {str(e)}"
        )

@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str) -> Dict[str, str]:
    try:
        success = chat_service.clear_conversation(conversation_id)
        if success:
            return {"message": "Conversation cleared successfully"}
        else:
            return {"message": "Conversation not found"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error clearing conversation: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    chat_available = chat_service.is_available()
    pinecone_available = chat_service.pinecone_service.is_available()

    if chat_available and pinecone_available:
        return HealthResponse(
            status="healthy",
            message="Chat service is running with full RAG capabilities",
        )
    elif chat_available:
        return HealthResponse(
            status="degraded",
            message="Chat service is running but RAG capabilities are disabled (Pinecone not configured)",
        )
    else:
        return HealthResponse(
            status="unhealthy",
            message="Chat service is not properly configured (missing API keys)",
        )
