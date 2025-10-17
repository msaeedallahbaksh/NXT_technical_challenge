"""
FastAPI application for AI-powered Product Discovery Assistant.

This is the main entry point for the backend API that provides:
- Server-Sent Events (SSE) for real-time communication
- AI agent integration with function calling
- Product search and recommendation system
- Context validation to prevent AI hallucination
"""

import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from database import init_db, get_session
from models import ChatMessage, SSEEvent, SessionContext
from ai_agent import AIAgent, MockAIAgent
from product_service import ProductService
from context_manager import ContextManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting AI Product Discovery Assistant...")
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Product Discovery Assistant",
    description="Real-time AI assistant with function calling and context validation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global services (in production, use dependency injection)
ai_agent = MockAIAgent() if os.getenv("AI_PROVIDER") == "simulate" else AIAgent()
product_service = ProductService()
context_manager = ContextManager()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/sessions")
async def create_session(session: AsyncSession = Depends(get_session)):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    
    # Initialize session context
    context = SessionContext(
        session_id=session_id,
        context_data={"created_at": datetime.utcnow().isoformat()}
    )
    session.add(context)
    await session.commit()
    
    return {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None  # Implement session expiration as needed
    }


@app.post("/api/chat/{session_id}/message")
async def send_message(
    session_id: str,
    message: ChatMessage,
    session: AsyncSession = Depends(get_session)
):
    """Send a message to the AI agent."""
    
    # Validate session exists
    if not await context_manager.session_exists(session_id, session):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store user message (optional - implement as needed)
    message_id = str(uuid.uuid4())
    
    return {
        "success": True,
        "message_id": message_id,
        "session_id": session_id
    }


@app.get("/api/stream/{session_id}")
async def stream_chat(
    session_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Server-Sent Events endpoint for real-time AI communication.
    
    This endpoint provides real-time streaming of:
    - AI text responses (chunked)
    - Function call executions  
    - Context updates
    - Error handling
    """
    
    # Validate session
    if not await context_manager.session_exists(session_id, session):
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_stream():
        """Generate SSE events."""
        try:
            # Send initial connection event
            event = SSEEvent(
                event="connection",
                data={"status": "connected", "session_id": session_id},
                id=str(uuid.uuid4())
            )
            yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
            
            # TODO: Implement your SSE streaming logic here
            # This is where you'll integrate with your AI agent
            
            # Example: Stream a welcome message
            welcome_chunks = [
                "Hello! I'm your AI shopping assistant. ",
                "I can help you search for products, ",
                "get detailed information, and manage your cart. ",
                "What would you like to find today?"
            ]
            
            for chunk in welcome_chunks:
                if await request.is_disconnected():
                    break
                    
                event = SSEEvent(
                    event="text_chunk",
                    data={"content": chunk, "partial": True},
                    id=str(uuid.uuid4())
                )
                yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
                
                # Realistic streaming delay
                await asyncio.sleep(0.1)
            
            # Send completion event
            event = SSEEvent(
                event="completion",
                data={"turn_id": str(uuid.uuid4()), "status": "complete"},
                id=str(uuid.uuid4())
            )
            yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
            
        except Exception as e:
            # Send error event
            error_event = SSEEvent(
                event="error",
                data={"error": str(e), "session_id": session_id},
                id=str(uuid.uuid4())
            )
            yield f"event: {error_event.event}\ndata: {json.dumps(error_event.data)}\nid: {error_event.id}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.get("/api/sessions/{session_id}/context")
async def get_session_context(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get the current session context."""
    context = await context_manager.get_context(session_id, session)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "context": context.context_data,
        "last_updated": context.updated_at.isoformat()
    }


# Function call endpoints (implement these based on your requirements)
@app.post("/api/functions/search_products")
async def search_products_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Search products function endpoint."""
    # TODO: Implement product search logic
    # This should use the ProductService and update context
    return {"success": True, "data": [], "message": "Not implemented yet"}


@app.post("/api/functions/show_product_details")
async def show_product_details_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Show product details function endpoint."""
    # TODO: Implement product details logic
    return {"success": True, "data": {}, "message": "Not implemented yet"}


@app.post("/api/functions/add_to_cart")
async def add_to_cart_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Add product to cart function endpoint."""
    # TODO: Implement cart management logic
    return {"success": True, "data": {}, "message": "Not implemented yet"}


@app.post("/api/functions/get_recommendations")
async def get_recommendations_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Get product recommendations function endpoint."""
    # TODO: Implement recommendations logic
    return {"success": True, "data": [], "message": "Not implemented yet"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )