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
def get_ai_agent() -> AIAgent:
    """Factory function to create the appropriate AI agent."""
    provider = os.getenv("AI_PROVIDER", "simulate").lower()
    
    if provider == "openai":
        try:
            from ai_agent import OpenAIAgent
            return OpenAIAgent()
        except ValueError as e:
            print(f"⚠️  Warning: {e}")
            print("⚠️  Falling back to MockAIAgent. Set OPENAI_API_KEY in .env to use OpenAI.")
            return MockAIAgent()
    elif provider == "anthropic":
        print("⚠️  Anthropic not implemented yet. Using MockAIAgent.")
        return MockAIAgent()
    else:
        print(f"ℹ️  Using MockAIAgent (AI_PROVIDER={provider})")
        return MockAIAgent()

ai_agent = get_ai_agent()
product_service = ProductService()
context_manager = ContextManager()

# Simple message queue for SSE (in production, use Redis or similar)
message_queues: Dict[str, asyncio.Queue] = {}


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
    
    # Create message queue for this session if it doesn't exist
    if session_id not in message_queues:
        message_queues[session_id] = asyncio.Queue()
    
    # Add message to queue for SSE stream to process
    await message_queues[session_id].put({
        "message": message.message,
        "context": message.context or {},
        "session_id": session_id
    })
    
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
        # Create message queue for this session if it doesn't exist
        if session_id not in message_queues:
            message_queues[session_id] = asyncio.Queue()
        
        queue = message_queues[session_id]
        
        try:
            # Send initial connection event
            event = SSEEvent(
                event="connection",
                data={"status": "connected", "session_id": session_id},
                id=str(uuid.uuid4())
            )
            yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
            
            # Stream a welcome message on initial connection
            welcome_chunks = [
                "Hello! I'm your AI shopping assistant. ",
                "I can help you search for products, ",
                "get detailed information, and manage your cart. ",
                "What would you like to find today?"
            ]
            
            for chunk in welcome_chunks:
                if await request.is_disconnected():
                    return
                    
                event = SSEEvent(
                    event="text_chunk",
                    data={"content": chunk, "partial": True},
                    id=str(uuid.uuid4())
                )
                yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
                await asyncio.sleep(0.05)
            
            # Send initial completion
            event = SSEEvent(
                event="completion",
                data={"turn_id": str(uuid.uuid4()), "status": "complete"},
                id=str(uuid.uuid4())
            )
            yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
            
            # Process messages from the queue
            while True:
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for message with timeout to check for disconnection
                    message_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # Get session context
                    ctx = await context_manager.get_context(session_id, session)
                    context_data = ctx.context_data if ctx else {}
                    
                    # Stream AI response
                    async for chunk in ai_agent.stream_response(
                        message=message_data["message"],
                        context=context_data,
                        session_id=session_id
                    ):
                        if await request.is_disconnected():
                            break
                            
                        event = SSEEvent(
                            event="text_chunk",
                            data={"content": chunk, "partial": True},
                            id=str(uuid.uuid4())
                        )
                        yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
                    
                    # Check if we should execute a function call (for Part 1, we'll trigger on keywords)
                    if "search" in message_data["message"].lower() or "find" in message_data["message"].lower():
                        # Extract search query (simple keyword extraction for Part 1)
                        query_words = message_data["message"].lower().split()
                        # Remove common words to get the search query
                        stop_words = {"search", "find", "for", "me", "the", "a", "an", "please", "can", "you", "show"}
                        query = " ".join([w for w in query_words if w not in stop_words])
                        
                        if query:
                            # Execute search function
                            function_call_event = SSEEvent(
                                event="function_call",
                                data={
                                    "function": "search_products",
                                    "parameters": {"query": query, "session_id": session_id}
                                },
                                id=str(uuid.uuid4())
                            )
                            yield f"event: {function_call_event.event}\ndata: {json.dumps(function_call_event.data)}\nid: {function_call_event.id}\n\n"
                    
                    # Send completion event
                    completion_event = SSEEvent(
                        event="completion",
                        data={"turn_id": str(uuid.uuid4()), "status": "complete"},
                        id=str(uuid.uuid4())
                    )
                    yield f"event: {completion_event.event}\ndata: {json.dumps(completion_event.data)}\nid: {completion_event.id}\n\n"
                    
                except asyncio.TimeoutError:
                    # No message received, continue loop to check for disconnection
                    continue
                except Exception as e:
                    # Send error event for message processing errors
                    error_event = SSEEvent(
                        event="error",
                        data={"error": str(e), "type": "message_processing"},
                        id=str(uuid.uuid4())
                    )
                    yield f"event: {error_event.event}\ndata: {json.dumps(error_event.data)}\nid: {error_event.id}\n\n"
            
        except Exception as e:
            # Send error event for stream errors
            error_event = SSEEvent(
                event="error",
                data={"error": str(e), "session_id": session_id, "type": "stream_error"},
                id=str(uuid.uuid4())
            )
            yield f"event: {error_event.event}\ndata: {json.dumps(error_event.data)}\nid: {error_event.id}\n\n"
        finally:
            # Clean up queue when connection closes
            if session_id in message_queues and message_queues[session_id].empty():
                del message_queues[session_id]
    
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


# Function call endpoints
@app.post("/api/functions/search_products")
async def search_products_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Search products function endpoint.
    
    This endpoint searches for products based on query and category,
    updates the search context, and returns results.
    """
    try:
        query = request.get("query", "")
        category = request.get("category")
        limit = request.get("limit", 10)
        session_id = request.get("session_id", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Search for products
        products = await product_service.search_products(
            query=query,
            category=category,
            limit=limit,
            session=session
        )
        
        # Track search results in context
        product_ids = [p.id for p in products]
        await context_manager.track_search_results(
            session_id=session_id,
            query=query,
            results=product_ids,
            category=category,
            session_db=session
        )
        
        # Convert products to dict format
        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "category": p.category,
                "image_url": p.image_url,
                "in_stock": p.in_stock,
                "rating": p.rating,
                "reviews_count": p.reviews_count
            }
            for p in products
        ]
        
        return {
            "success": True,
            "data": {
                "products": products_data,
                "total_results": len(products_data),
                "search_context": {
                    "query": query,
                    "category": category,
                    "results_cached": True
                }
            },
            "context_updated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")


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