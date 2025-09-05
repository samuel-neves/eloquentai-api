from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    session_id: str
    token: str
    user_type: str
    message: str

class SessionResponse(BaseModel):
    session_id: str
    user_type: str
    is_authenticated: bool
    conversation_count: int
    session_duration: str
    last_activity: str

def get_session_from_header(
    authorization: Optional[str] = Header(None),
) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None

    try:
        auth_type, token = authorization.split(" ", 1)

        if auth_type.lower() == "bearer":
            return auth_service.verify_jwt_token(token)
        elif auth_type.lower() == "session":
            return auth_service.get_session(token)
        else:
            return None
    except ValueError:
        return None

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    try:
        session_id = auth_service.create_authenticated_session(
            request.email, request.password
        )

        if not session_id:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = auth_service.generate_jwt_token(session_id)

        return LoginResponse(
            success=True,
            session_id=session_id,
            token=token,
            user_type="authenticated",
            message="Login successful",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/anonymous", response_model=LoginResponse)
async def create_anonymous_session() -> LoginResponse:
    try:
        session_id = auth_service.create_session()
        token = auth_service.generate_jwt_token(session_id)

        return LoginResponse(
            success=True,
            session_id=session_id,
            token=token,
            user_type="anonymous",
            message="Anonymous session created",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create anonymous session: {str(e)}"
        )

@router.get("/session", response_model=SessionResponse)
async def get_session_info(
    session: Optional[Dict[str, Any]] = Depends(get_session_from_header),
) -> SessionResponse:
    if not session:
        raise HTTPException(
            status_code=401,
            detail="No valid session found. Please login or create an anonymous session.",
        )

    stats = auth_service.get_session_stats(session["session_id"])

    return SessionResponse(
        session_id=session["session_id"],
        user_type=session.get("user_type", "anonymous"),
        is_authenticated=session.get("is_authenticated", False),
        conversation_count=stats.get("conversation_count", 0),
        session_duration=stats.get("session_duration", "0:00:00"),
        last_activity=stats.get("last_activity", ""),
    )

@router.post("/logout")
async def logout(
    session: Optional[Dict[str, Any]] = Depends(get_session_from_header),
) -> Dict[str, str]:
    if not session:
        raise HTTPException(status_code=401, detail="No active session found")

    success = auth_service.delete_session(session["session_id"])

    if success:
        return {"message": "Logout successful"}
    else:
        return {"message": "Session already expired"}

@router.get("/stats")
async def get_auth_stats() -> Dict[str, Any]:
    expired_count = auth_service.cleanup_expired_sessions()

    stats = auth_service.get_all_sessions_stats()
    stats["expired_sessions_cleaned"] = expired_count

    return stats

@router.get("/demo-credentials")
async def get_demo_credentials() -> Dict[str, str]:
    return {
        "email": "demo@fintech.com",
        "password": "demo123",
        "note": "Use these credentials to test authenticated features",
        "anonymous_option": "Use POST /auth/anonymous for anonymous access",
    }
