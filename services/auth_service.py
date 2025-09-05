import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import jwt
from config import settings

class AuthService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        self.jwt_secret = getattr(settings, "jwt_secret", self._generate_jwt_secret())
        self.session_timeout = timedelta(hours=24)

        self._create_default_users()

    def _generate_jwt_secret(self) -> str:
        return secrets.token_urlsafe(32)

    def _create_default_users(self):
        self.users["anonymous"] = {
            "user_id": "anonymous",
            "username": "anonymous",
            "email": "anonymous@example.com",
            "is_authenticated": False,
            "created_at": datetime.utcnow(),
            "user_type": "anonymous",
        }

        demo_password = self._hash_password("demo123")
        self.users["demo@fintech.com"] = {
            "user_id": str(uuid.uuid4()),
            "username": "demo_user",
            "email": "demo@fintech.com",
            "password_hash": demo_password,
            "is_authenticated": True,
            "created_at": datetime.utcnow(),
            "user_type": "authenticated",
            "account_status": "active",
        }

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_session(self, user_id: str = "anonymous", user_data: Dict = None) -> str:
        session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "conversation_count": 0,
            "is_authenticated": (
                user_data.get("is_authenticated", False) if user_data else False
            ),
            "user_type": (
                user_data.get("user_type", "anonymous") if user_data else "anonymous"
            ),
        }

        if user_data:
            session_data.update(user_data)

        self.sessions[session_id] = session_data
        return session_id

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        if email not in self.users:
            return None

        user = self.users[email]
        if not user.get("is_authenticated", False):
            return None

        password_hash = self._hash_password(password)
        if user["password_hash"] != password_hash:
            return None

        user_data = user.copy()
        del user_data["password_hash"]
        return user_data

    def create_authenticated_session(self, email: str, password: str) -> Optional[str]:
        user_data = self.authenticate_user(email, password)
        if not user_data:
            return None

        return self.create_session(user_data["user_id"], user_data)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        if self._is_session_expired(session):
            self.delete_session(session_id)
            return None

        session["last_activity"] = datetime.utcnow()
        return session

    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        last_activity = session.get("last_activity", datetime.utcnow())
        return datetime.utcnow() - last_activity > self.session_timeout

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def update_session_activity(self, session_id: str, activity_data: Dict = None):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["last_activity"] = datetime.utcnow()

            if activity_data:
                if activity_data.get("new_conversation"):
                    session["conversation_count"] = (
                        session.get("conversation_count", 0) + 1
                    )

                for key, value in activity_data.items():
                    if key not in ["session_id", "user_id", "created_at"]:
                        session[key] = value

    def generate_jwt_token(self, session_id: str) -> Optional[str]:
        session = self.get_session(session_id)
        if not session:
            return None

        payload = {
            "session_id": session_id,
            "user_id": session["user_id"],
            "user_type": session.get("user_type", "anonymous"),
            "exp": datetime.utcnow() + self.session_timeout,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            session_id = payload.get("session_id")

            if session_id:
                return self.get_session(session_id)
            return None

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {}

        return {
            "session_id": session_id,
            "user_type": session.get("user_type", "anonymous"),
            "conversation_count": session.get("conversation_count", 0),
            "session_duration": str(datetime.utcnow() - session["created_at"]),
            "last_activity": session["last_activity"].isoformat(),
            "is_authenticated": session.get("is_authenticated", False),
        }

    def cleanup_expired_sessions(self):
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        return len(expired_sessions)

    def get_all_sessions_stats(self) -> Dict[str, Any]:
        active_sessions = len(self.sessions)
        authenticated_sessions = sum(
            1 for s in self.sessions.values() if s.get("is_authenticated", False)
        )
        anonymous_sessions = active_sessions - authenticated_sessions

        return {
            "total_active_sessions": active_sessions,
            "authenticated_sessions": authenticated_sessions,
            "anonymous_sessions": anonymous_sessions,
            "total_users": len(self.users),
        }
