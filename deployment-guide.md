# EloquentAI API Deployment Guide

## Prerequisites for External Access

### 1. External Service Accounts Required

#### OpenAI Account
- **Sign up**: https://platform.openai.com/
- **Get API Key**: https://platform.openai.com/api-keys
- **Add billing**: Required for API usage
- **Models needed**: 
  - `gpt-3.5-turbo` (for chat responses)
  - `text-embedding-ada-002` (for vector embeddings)

#### Pinecone Account
- **Sign up**: https://app.pinecone.io/
- **Get API Key**: From your Pinecone dashboard
- **Create Index**: 
  - Name: `eloquentai-index` (or your preferred name)
  - Dimensions: `1536` (required for OpenAI embeddings)
  - Metric: `cosine` (recommended)
  - Environment: Note your environment (e.g., `us-east-1-aws`)

### 2. Environment Configuration

Create a `.env` file in the `/api` directory:

```bash
# Copy from env-template.txt and fill in your actual values
cp env-template.txt .env
```

Required environment variables:
```env
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
PINECONE_API_KEY=your-actual-pinecone-key-here  
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=eloquentai-index
```

### 3. System Requirements

#### Python Environment
```bash
# Python 3.8+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

#### For Production Deployment
```bash
# Additional production dependencies
pip install gunicorn
pip install python-multipart
```

### 4. Network Configuration

#### Local Development
```bash
# Default configuration (localhost only)
python start.py
# API available at: http://localhost:8000
```

#### External Access
For external services to access your API, you need:

**Option 1: Cloud Deployment (Recommended)**
- Deploy to cloud services like:
  - **Heroku**: Easy deployment with git
  - **Railway**: Simple Python deployment
  - **DigitalOcean App Platform**: Managed hosting
  - **AWS EC2/ECS**: Full control
  - **Google Cloud Run**: Serverless containers
  - **Vercel**: For serverless functions

**Option 2: VPS/Server Deployment**
```bash
# Install on your server
git clone your-repo
cd eloquentai/api
pip install -r requirements.txt

# Run with Gunicorn for production
gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Option 3: Local with Tunneling (Development Only)**
```bash
# Using ngrok for temporary external access
ngrok http 8000
# Provides public URL like: https://abc123.ngrok.io
```

### 5. Security Considerations

#### Environment Variables Security
- **Never commit `.env` to version control**
- Use environment variable injection in production
- Rotate API keys regularly

#### CORS Configuration
Update `main.py` for production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify your domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

#### Additional Security Headers
```python
# Add to main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

### 6. Testing External Access

Once deployed, test your endpoints:

```bash
# Health check
curl https://your-api-url.com/health

# Chat endpoint
curl -X POST https://your-api-url.com/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'

# Document upload
curl -X POST https://your-api-url.com/api/documents/upload \
  -H "Content-Type: application/json" \
  -d '{"content": "Test document", "title": "Test"}'
```

### 7. Monitoring and Logging

Add logging to your application:
```python
# Add to main.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
```

## Summary Checklist

- [ ] OpenAI account with API key and billing set up
- [ ] Pinecone account with index created (1536 dimensions)
- [ ] Environment variables configured
- [ ] Choose deployment platform
- [ ] Configure CORS for your domains
- [ ] Set up monitoring and logging
- [ ] Test all endpoints after deployment

Your API will then be accessible from external services at your deployed URL!
