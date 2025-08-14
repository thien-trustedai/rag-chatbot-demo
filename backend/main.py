#!/usr/bin/env python3
"""
FastAPI Backend for PDF RAG Chat System
Wraps existing functionality without changing logic
"""

import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our existing modules - NO LOGIC CHANGES
from extractors.parallel_pdf_extractor import ParallelPDFExtractor
from rag.index_to_chromadb import PDFMetadataIndexer
from rag.rag_query import RAGQuerySystem

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PDF RAG Chat API",
    description="API for PDF extraction, indexing, and chat",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
UPLOAD_DIR = Path("uploads")
EXTRACTION_DIR = Path("extractions")
UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACTION_DIR.mkdir(exist_ok=True)

# Store active sessions
sessions: Dict[str, Dict[str, Any]] = {}


# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    document_id: str  # Changed from session_id to match frontend
    n_results: Optional[int] = 10


class ChatResponse(BaseModel):
    response: str
    references: List[Dict[str, Any]]


class ProcessingStatus(BaseModel):
    status: str
    progress: int
    message: str
    document_id: Optional[str] = None


class DocumentInfo(BaseModel):
    document_id: str
    total_chunks: int
    total_pages: int
    total_text_length: int
    total_images: int
    pages: List[int]


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_processed: int
    message: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PDF RAG Chat API is running"}


@app.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.
    Uses existing extraction logic without changes.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate unique document ID
    document_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{document_id}.pdf"
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create extraction directory
    extraction_dir = EXTRACTION_DIR / document_id
    extraction_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Extract PDF using existing logic
        extractor = ParallelPDFExtractor(
            pdf_path=str(upload_path),
            output_directory=str(extraction_dir),
            max_workers=4
        )
        
        extraction_summary = extractor.extract()
        
        # Step 2: Index to ChromaDB using existing logic
        indexer = PDFMetadataIndexer(
            collection_name=f"doc_{document_id}",
            use_openai=True,
            azure=True
        )
        
        # Clear any existing data for this document
        indexer.clear_collection()
        
        # Index the extracted content
        metadata_path = extraction_dir / "metadata.json"
        indexing_stats = indexer.index_from_metadata(
            str(metadata_path),
            base_dir=str(extraction_dir)
        )
        
        # Store session info
        sessions[document_id] = {
            "document_id": document_id,
            "filename": file.filename,
            "upload_path": str(upload_path),
            "extraction_dir": str(extraction_dir),
            "collection_name": f"doc_{document_id}",
            "extraction_summary": extraction_summary,
            "indexing_stats": indexing_stats,
            "created_at": datetime.now().isoformat()
        }
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunks_processed=indexing_stats.get("total_documents", 0),
            message="PDF processed and indexed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/document/{document_id}/info", response_model=DocumentInfo)
async def get_document_info(document_id: str):
    """Get information about a processed document."""
    if document_id not in sessions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    session = sessions[document_id]
    summary = session.get("extraction_summary", {})
    indexing_stats = session.get("indexing_stats", {})
    
    # Calculate total text length from metadata
    metadata_path = Path(session["extraction_dir"]) / "metadata.json"
    total_text_length = 0
    pages_list = []
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            for section in metadata.get("sections", []):
                total_text_length += len(section.get("text", ""))
            # Get unique page numbers
            pages_set = set()
            for section in metadata.get("sections", []):
                if "page_number" in section:
                    pages_set.add(section["page_number"])
            pages_list = sorted(list(pages_set))
    
    # If no pages found, create a list based on total_pages
    if not pages_list and summary.get("total_pages", 0) > 0:
        pages_list = list(range(1, summary.get("total_pages", 0) + 1))
    
    return DocumentInfo(
        document_id=document_id,
        total_chunks=indexing_stats.get("total_documents", 0),
        total_pages=summary.get("total_pages", 0),
        total_text_length=total_text_length,
        total_images=summary.get("total_figures", 0) + summary.get("total_tables", 0),
        pages=pages_list
    )


@app.get("/pdf/{document_id}")
async def get_pdf(document_id: str):
    """Serve the PDF file for viewing."""
    if document_id not in sessions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    pdf_path = sessions[document_id]["upload_path"]
    if not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={sessions[document_id]['filename']}"}
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Chat with a processed document.
    Uses existing RAG query logic without changes.
    """
    if message.document_id not in sessions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    session = sessions[message.document_id]
    collection_name = session["collection_name"]
    extraction_dir = session["extraction_dir"]
    
    try:
        # Initialize RAG system using existing logic
        rag = RAGQuerySystem(
            db_path="./chroma_db",
            collection_name=collection_name,
            output_dir=extraction_dir,
            use_azure=True
        )
        
        # Get conversation history if it exists
        if "conversation_history" not in session:
            session["conversation_history"] = []
        
        # Query using existing logic - returns (answer, references)
        answer, references = rag.query(
            message.message,
            n_results=message.n_results,
            verbose=False,
            conversation_history=session["conversation_history"],
            return_references=True
        )
        
        # Update conversation history
        session["conversation_history"].append({
            "role": "user",
            "content": message.message
        })
        session["conversation_history"].append({
            "role": "assistant",
            "content": answer
        })
        
        # Keep history manageable
        if len(session["conversation_history"]) > 20:
            session["conversation_history"] = session["conversation_history"][-20:]
        
        return ChatResponse(
            response=answer,
            references=references
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.websocket("/ws/{document_id}")
async def websocket_chat(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time chat.
    Uses existing RAG logic without changes.
    """
    await websocket.accept()
    
    if document_id not in sessions:
        await websocket.send_json({
            "type": "error",
            "message": "Document not found"
        })
        await websocket.close()
        return
    
    session = sessions[document_id]
    collection_name = session["collection_name"]
    extraction_dir = session["extraction_dir"]
    
    # Initialize RAG system
    try:
        rag = RAGQuerySystem(
            db_path="./chroma_db",
            collection_name=collection_name,
            output_dir=extraction_dir,
            use_azure=True
        )
        
        # Initialize conversation history for this websocket session
        conversation_history = []
        
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to chat",
            "document_info": {
                "filename": session["filename"],
                "pages": session["extraction_summary"].get("total_pages", 0)
            }
        })
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                if data.get("type") == "chat":
                    message = data.get("message", "")
                    
                    # Send processing status
                    await websocket.send_json({
                        "type": "processing",
                        "message": "Thinking..."
                    })
                    
                    # Query using existing logic
                    answer, references = rag.query(
                        message,
                        n_results=10,
                        verbose=False,
                        conversation_history=conversation_history,
                        return_references=True
                    )
                    
                    # Update conversation history
                    conversation_history.append({
                        "role": "user",
                        "content": message
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": answer
                    })
                    
                    # Keep history manageable
                    if len(conversation_history) > 20:
                        conversation_history = conversation_history[-20:]
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "message": answer,
                        "references": references
                    })
                    
                elif data.get("type") == "reset":
                    conversation_history = []
                    await websocket.send_json({
                        "type": "reset",
                        "message": "Conversation reset"
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
                
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to initialize chat: {str(e)}"
        })
        await websocket.close()


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": [
            {
                "document_id": doc_id,
                "filename": info["filename"],
                "created_at": info["created_at"]
            }
            for doc_id, info in sessions.items()
        ]
    }


@app.delete("/session/{document_id}")
async def delete_session(document_id: str):
    """Delete a session and its data."""
    if document_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[document_id]
    
    # Clean up files
    try:
        upload_path = Path(session["upload_path"])
        if upload_path.exists():
            upload_path.unlink()
        
        extraction_dir = Path(session["extraction_dir"])
        if extraction_dir.exists():
            import shutil
            shutil.rmtree(extraction_dir)
        
        # Remove from sessions
        del sessions[document_id]
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)