# EloquentAI Backend

A FastAPI-based backend for an AI-powered chatbot with Retrieval-Augmented Generation (RAG) capabilities using Pinecone vector database.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Chat Functionality**: RESTful APIs for chat interactions
- **RAG Integration**: Retrieval-Augmented Generation using Pinecone vector database
- **Document Management**: Upload, search, and manage documents in vector database
- **OpenAI Integration**: Uses GPT-3.5-turbo for chat responses
- **Vector Embeddings**: Text-embedding-ada-002 for document embeddings

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the api directory with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=your_pinecone_environment_here
   PINECONE_INDEX_NAME=your_pinecone_index_name_here
   ```

3. **Run the Server**:
   ```bash
   python main.py
   ```
   Or with uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Chat Endpoints

- `POST /api/chat/message` - Send a message and get AI response
- `GET /api/chat/conversation/{conversation_id}` - Get conversation history
- `DELETE /api/chat/conversation/{conversation_id}` - Clear conversation
- `GET /api/chat/health` - Chat service health check

### Document Endpoints

- `POST /api/documents/upload` - Upload document content
- `POST /api/documents/upload-file` - Upload text file
- `GET /api/documents/search` - Search documents by query
- `DELETE /api/documents/{document_id}` - Delete document
- `GET /api/documents/health` - Documents service health check

### General Endpoints

- `GET /` - Root endpoint
- `GET /health` - Global health check

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
api/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── models.py            # Pydantic models
├── requirements.txt     # Python dependencies
├── services/            # Business logic services
│   ├── __init__.py
│   ├── chat_service.py  # Chat and RAG logic
│   └── pinecone_service.py  # Vector database operations
└── routes/              # API route handlers
    ├── __init__.py
    ├── chat.py          # Chat endpoints
    └── documents.py     # Document endpoints
```

## Usage Examples

### Send a Chat Message

```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "conversation_id": "optional-conversation-id"
  }'
```

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Machine learning is a subset of artificial intelligence...",
    "title": "Introduction to ML",
    "metadata": {"author": "AI Assistant"}
  }'
```

### Search Documents

```bash
curl -X GET "http://localhost:8000/api/documents/search?query=machine%20learning&top_k=5"
```

## Notes

- Make sure to set up your Pinecone index before running the application
- The Pinecone index should be configured for 1536 dimensions (OpenAI embedding size)
- For production use, properly configure CORS origins and add authentication
- Consider implementing rate limiting and request validation for production deployment
