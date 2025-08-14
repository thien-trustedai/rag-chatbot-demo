# PDF RAG Chat API Documentation

## Overview

FastAPI backend that provides REST API and WebSocket endpoints for PDF processing and chat functionality. The API wraps the existing PDF extraction and RAG logic without changing the core functionality.

## Base URL

```
http://localhost:8000
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### 1. Upload and Process PDF

**POST** `/upload-pdf`

Upload a PDF file for extraction and indexing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: PDF file

**Response:**
```json
{
  "status": "completed",
  "progress": 100,
  "message": "PDF processed and indexed successfully",
  "document_id": "uuid-string"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/upload-pdf" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 2. Get Document Information

**GET** `/document/{document_id}`

Get information about a processed document.

**Response:**
```json
{
  "document_id": "uuid-string",
  "filename": "document.pdf",
  "pages": 10,
  "figures": 5,
  "tables": 3,
  "sections": 15,
  "indexed": true,
  "created_at": "2024-01-01T12:00:00"
}
```

### 3. Get PDF File

**GET** `/pdf/{document_id}`

Retrieve the original PDF file for viewing.

**Response:**
- Content-Type: `application/pdf`
- PDF file binary

### 4. Chat with Document

**POST** `/chat`

Send a chat message and receive RAG-powered response.

**Request:**
```json
{
  "message": "What is the main topic of this document?",
  "session_id": "document-uuid",
  "n_results": 5
}
```

**Response:**
```json
{
  "response": "The main topic is...",
  "references": [
    {
      "type": "text",
      "content": "Reference text...",
      "page_number": 1,
      "metadata": {}
    }
  ],
  "session_id": "document-uuid"
}
```

### 5. WebSocket Chat

**WebSocket** `/ws/{document_id}`

Real-time chat interface using WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/document-uuid');
```

**Send Message:**
```json
{
  "type": "chat",
  "message": "Your question here"
}
```

**Receive Response:**
```json
{
  "type": "response",
  "message": "Answer from the system",
  "references": [...]
}
```

**Message Types:**
- `connected` - Initial connection confirmation
- `processing` - Indicates processing status
- `response` - Chat response with references
- `error` - Error message
- `reset` - Reset conversation

### 6. List Sessions

**GET** `/sessions`

List all active document sessions.

**Response:**
```json
{
  "sessions": [
    {
      "document_id": "uuid-string",
      "filename": "document.pdf",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### 7. Delete Session

**DELETE** `/session/{document_id}`

Delete a session and its associated data.

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

### 8. Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 2,
  "timestamp": "2024-01-01T12:00:00"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (e.g., invalid file type)
- `404` - Not Found (e.g., document not found)
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Authentication

Currently, the API does not require authentication. In production, you should add:
- API key authentication
- JWT tokens
- Rate limiting

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000` (React default)
- `http://localhost:3001` (Alternative port)

Modify the CORS settings in `main.py` for production use.

## Running the Server

### Development Mode

```bash
cd backend
./run_server.sh
```

Or directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Environment Variables

Required environment variables (in `.env` file):

```env
# Azure OpenAI Configuration
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBEDDING_API_KEY=your_key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

## Frontend Integration Example

```javascript
// Upload PDF
const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/upload-pdf', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};

// Chat with document
const sendMessage = async (message, sessionId) => {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
      n_results: 5
    })
  });
  
  return await response.json();
};

// WebSocket connection
const connectWebSocket = (documentId) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/${documentId}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
  };
  
  // Send message
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Your question'
  }));
};
```

## Notes

- The API uses the existing PDF extraction and RAG logic without modifications
- All processing is done server-side using the same modules
- Sessions are stored in memory (use Redis for production)
- File uploads are stored temporarily in the `uploads/` directory
- Extraction results are stored in the `extractions/` directory