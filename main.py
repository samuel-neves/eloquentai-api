from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, documents, auth, fintech
from config import settings

app = FastAPI(
    title="EloquentAI Fintech Chatbot",
    description="AI-powered fintech chatbot with RAG capabilities for answering financial services questions",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(fintech.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to EloquentAI Fintech Chatbot",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "AI-powered chat with RAG",
            "Fintech FAQ support",
            "User authentication",
            "Category-based queries",
            "Vector database search",
        ],
        "endpoints": {
            "chat": "/api/chat",
            "documents": "/api/documents",
            "auth": "/api/auth",
            "fintech": "/api/fintech",
        },
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "EloquentAI Backend is running",
        "services": {
            "chat": "healthy",
            "documents": "healthy",
            "vector_db": "connected",
        },
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
