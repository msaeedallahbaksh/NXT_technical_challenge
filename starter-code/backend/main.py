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
                    user_message = message_data["message"]
                    
                    # Store user message in conversation history
                    from models import ConversationMessage
                    user_msg_record = ConversationMessage(
                        session_id=session_id,
                        role="user",
                        content=user_message
                    )
                    session.add(user_msg_record)
                    await session.commit()
                    
                    # Get session context
                    ctx = await context_manager.get_context(session_id, session)
                    context_data = ctx.context_data if ctx else {}
                    
                    # Retrieve conversation history (last 20 messages)
                    from sqlmodel import select
                    history_statement = select(ConversationMessage).where(
                        ConversationMessage.session_id == session_id
                    ).order_by(ConversationMessage.timestamp).limit(20)
                    history_result = await session.execute(history_statement)
                    history_messages = history_result.scalars().all()
                    
                    # Convert to OpenAI format (exclude the current message we just added)
                    conversation_history = []
                    for msg in history_messages[:-1]:  # Exclude the last message (current user message)
                        if msg.role == "tool":
                            # Tool result message - OpenAI expects specific format
                            tool_data = json.loads(msg.tool_calls) if msg.tool_calls else []
                            if tool_data:
                                conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_data[0]["id"],
                                    "content": msg.content
                                })
                        elif msg.role == "assistant" and msg.tool_calls:
                            # Assistant message with tool calls
                            tool_calls_data = json.loads(msg.tool_calls)
                            # Format tool calls for OpenAI
                            formatted_tool_calls = []
                            for tc in tool_calls_data:
                                formatted_tool_calls.append({
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["function"],
                                        "arguments": json.dumps(tc["arguments"])
                                    }
                                })
                            
                            conversation_history.append({
                                "role": "assistant",
                                "content": msg.content or None,
                                "tool_calls": formatted_tool_calls
                            })
                        else:
                            # Regular user or assistant message
                            conversation_history.append({
                                "role": msg.role,
                                "content": msg.content
                            })
                    
                    # Track assistant response content
                    assistant_response_text = ""
                    assistant_tool_calls = []
                    tool_results = []  # Track tool execution results
                    
                    # Stream AI response with real-time function calling
                    async for response_chunk in ai_agent.stream_response(
                        message=user_message,
                        context=context_data,
                        session_id=session_id,
                        conversation_history=conversation_history
                    ):
                        if await request.is_disconnected():
                            break
                        
                        chunk_type = response_chunk.get("type")
                        chunk_content = response_chunk.get("content")
                        
                        # Handle text content
                        if chunk_type == "text":
                            assistant_response_text += chunk_content
                            event = SSEEvent(
                                event="text_chunk",
                                data={"content": chunk_content, "partial": True},
                                id=str(uuid.uuid4())
                            )
                            yield f"event: {event.event}\ndata: {json.dumps(event.data)}\nid: {event.id}\n\n"
                        
                        # Handle AI-detected tool calls
                        elif chunk_type == "tool_call":
                            function_name = chunk_content["function"]
                            arguments = chunk_content["arguments"]
                            tool_call_id = chunk_content["id"]
                            
                            # Track tool call
                            assistant_tool_calls.append({
                                "id": tool_call_id,
                                "function": function_name,
                                "arguments": arguments
                            })
                            
                            # Notify frontend that function is being called
                            function_call_event = SSEEvent(
                                event="function_call",
                                data={
                                    "function": function_name,
                                    "parameters": arguments,
                                    "tool_call_id": tool_call_id
                                },
                                id=str(uuid.uuid4())
                            )
                            yield f"event: {function_call_event.event}\ndata: {json.dumps(function_call_event.data)}\nid: {function_call_event.id}\n\n"
                            
                            # Auto-execute all functions
                            try:
                                function_result = None
                                
                                if function_name == "search_products":
                                    # Execute search
                                    query = arguments.get("query", "")
                                    category = arguments.get("category")
                                    limit = arguments.get("limit", 10)
                                    
                                    products = await product_service.search_products(
                                        query=query,
                                        category=category,
                                        limit=limit,
                                        session=session
                                    )
                                    
                                    # Track search results in context
                                    product_ids = [p.id for p in products]
                                    await context_manager.track_search_results(
                                        session_id, product_ids, session
                                    )
                                    
                                    function_result = {
                                        "success": True,
                                        "data": {
                                            "products": [p.model_dump(mode='json') for p in products],
                                            "total": len(products),
                                            "query": query
                                        },
                                        "context_updated": True
                                    }
                                
                                elif function_name == "show_product_details":
                                    product_id = arguments.get("product_id")
                                    include_recs = arguments.get("include_recommendations", True)
                                    
                                    # Validate product_id is in recent context
                                    ctx = await context_manager.get_context(session_id, session)
                                    if ctx and not await context_manager.validate_product_id(
                                        session_id, product_id, session
                                    ):
                                        function_result = {
                                            "success": False,
                                            "error": "Product not found in recent search results"
                                        }
                                    else:
                                        product = await product_service.get_product_by_id(
                                            product_id, session
                                        )
                                        
                                        if not product:
                                            function_result = {
                                                "success": False,
                                                "error": "Product not found"
                                            }
                                        else:
                                            result_data = {"product": product.model_dump(mode='json')}
                                            
                                            if include_recs:
                                                recommendations = await product_service.get_recommendations(
                                                    based_on_product_id=product.id,
                                                    limit=4,
                                                    session=session
                                                )
                                                result_data["recommendations"] = [
                                                    r.model_dump(mode='json') for r in recommendations
                                                ]
                                            
                                            function_result = {
                                                "success": True,
                                                "data": result_data
                                            }
                                
                                elif function_name == "get_recommendations":
                                    based_on = arguments.get("based_on", "")
                                    max_results = arguments.get("max_results", 5)
                                    
                                    # Check if based_on is a product ID or category
                                    product = await product_service.get_product_by_id(
                                        product_id=based_on,
                                        session=session
                                    )
                                    
                                    if product:
                                        # based_on is a product ID
                                        recommendations = await product_service.get_recommendations(
                                            based_on_product_id=product.id,
                                            limit=max_results,
                                            session=session
                                        )
                                        recommendation_context = {
                                            "based_on_product": product.name,
                                            "based_on_category": product.category
                                        }
                                    else:
                                        # based_on might be a category - search by category
                                        from models import ProductCategory
                                        try:
                                            category = ProductCategory(based_on.lower())
                                            recommendations = await product_service.search_products(
                                                query="",
                                                category=category,
                                                limit=max_results,
                                                session=session
                                            )
                                            recommendation_context = {
                                                "based_on_category": based_on
                                            }
                                        except ValueError:
                                            # Not a valid category or product ID
                                            function_result = {
                                                "success": False,
                                                "error": f"'{based_on}' is not a valid product ID or category"
                                            }
                                            recommendations = []
                                            recommendation_context = {}
                                    
                                    if recommendations:
                                        function_result = {
                                            "success": True,
                                            "data": {
                                                "recommendations": [r.model_dump(mode='json') for r in recommendations],
                                                "recommendation_context": recommendation_context,
                                                "total": len(recommendations)
                                            }
                                        }
                                
                                elif function_name == "add_to_cart":
                                    # Auto-execute add to cart
                                    from models import CartItem
                                    from sqlmodel import select
                                    
                                    product_id = arguments.get("product_id")
                                    quantity = arguments.get("quantity", 1)
                                    
                                    if not product_id:
                                        function_result = {
                                            "success": False,
                                            "error": {
                                                "code": "MISSING_PRODUCT_ID",
                                                "message": "Product ID is required"
                                            }
                                        }
                                    else:
                                        # Get product to check stock and price
                                        product = await product_service.get_product_by_id(
                                            product_id=product_id,
                                            session=session
                                        )
                                        
                                        if not product:
                                            function_result = {
                                                "success": False,
                                                "error": {
                                                    "code": "PRODUCT_NOT_FOUND",
                                                    "message": f"Product with ID '{product_id}' was not found"
                                                }
                                            }
                                        elif not product.in_stock:
                                            function_result = {
                                                "success": False,
                                                "error": {
                                                    "code": "OUT_OF_STOCK",
                                                    "message": f"Product '{product.name}' is currently out of stock"
                                                }
                                            }
                                        elif product.stock_quantity < quantity:
                                            function_result = {
                                                "success": False,
                                                "error": {
                                                    "code": "INSUFFICIENT_STOCK",
                                                    "message": f"Only {product.stock_quantity} units available",
                                                    "details": {
                                                        "requested": quantity,
                                                        "available": product.stock_quantity
                                                    }
                                                }
                                            }
                                        else:
                                            # Check if item already in cart
                                            statement = select(CartItem).where(
                                                CartItem.session_id == session_id,
                                                CartItem.product_id == product_id
                                            )
                                            result = await session.execute(statement)
                                            existing_item = result.scalar_one_or_none()
                                            
                                            if existing_item:
                                                # Update existing cart item
                                                existing_item.quantity += quantity
                                                existing_item.total_price = existing_item.quantity * product.price
                                                session.add(existing_item)
                                                await session.commit()
                                                await session.refresh(existing_item)
                                                cart_item = existing_item
                                            else:
                                                # Create new cart item
                                                cart_item = CartItem(
                                                    session_id=session_id,
                                                    product_id=product_id,
                                                    quantity=quantity,
                                                    unit_price=product.price,
                                                    total_price=quantity * product.price
                                                )
                                                session.add(cart_item)
                                                await session.commit()
                                                await session.refresh(cart_item)
                                            
                                            # Calculate cart summary
                                            statement = select(CartItem).where(CartItem.session_id == session_id)
                                            result = await session.execute(statement)
                                            all_cart_items = result.scalars().all()
                                            
                                            total_items = sum(item.quantity for item in all_cart_items)
                                            subtotal = sum(item.total_price for item in all_cart_items)
                                            estimated_tax = round(subtotal * 0.1, 2)
                                            estimated_total = round(subtotal + estimated_tax, 2)
                                            
                                            function_result = {
                                                "success": True,
                                                "data": {
                                                    "cart_item": {
                                                        "id": cart_item.id,
                                                        "product_id": cart_item.product_id,
                                                        "product_name": product.name,
                                                        "quantity": cart_item.quantity,
                                                        "unit_price": float(cart_item.unit_price),
                                                        "total_price": float(cart_item.total_price)
                                                    },
                                                    "cart_summary": {
                                                        "total_items": total_items,
                                                        "total_products": len(all_cart_items),
                                                        "subtotal": float(subtotal),
                                                        "estimated_tax": float(estimated_tax),
                                                        "estimated_total": float(estimated_total)
                                                    }
                                                }
                                            }
                                
                                else:
                                    function_result = {
                                        "success": False,
                                        "error": f"Unknown function: {function_name}"
                                    }
                                
                                # Track tool result for conversation history
                                tool_results.append({
                                    "tool_call_id": tool_call_id,
                                    "function": function_name,
                                    "result": function_result
                                })
                                
                                # Send function result back to frontend
                                result_event = SSEEvent(
                                    event="function_result",
                                    data={
                                        "function": function_name,
                                        "tool_call_id": tool_call_id,
                                        "result": function_result
                                    },
                                    id=str(uuid.uuid4())
                                )
                                yield f"event: {result_event.event}\ndata: {json.dumps(result_event.data)}\nid: {result_event.id}\n\n"
                                
                            except Exception as func_error:
                                # Send function error
                                error_result = SSEEvent(
                                    event="error",
                                    data={
                                        "function": function_name,
                                        "tool_call_id": tool_call_id,
                                        "error": str(func_error),
                                        "type": "function_error"
                                    },
                                    id=str(uuid.uuid4())
                                )
                                yield f"event: {error_result.event}\ndata: {json.dumps(error_result.data)}\nid: {error_result.id}\n\n"
                        
                        # Handle AI errors
                        elif chunk_type == "error":
                            error_event = SSEEvent(
                                event="error",
                                data={"error": chunk_content, "type": "ai_error"},
                                id=str(uuid.uuid4())
                            )
                            yield f"event: {error_event.event}\ndata: {json.dumps(error_event.data)}\nid: {error_event.id}\n\n"
                    
                    # Store assistant response in conversation history
                    if assistant_response_text or assistant_tool_calls:
                        assistant_msg_record = ConversationMessage(
                            session_id=session_id,
                            role="assistant",
                            content=assistant_response_text or "",
                            tool_calls=json.dumps(assistant_tool_calls) if assistant_tool_calls else None
                        )
                        session.add(assistant_msg_record)
                        await session.commit()
                    
                    # Store tool results as separate messages (role="tool")
                    for tool_result in tool_results:
                        tool_msg_record = ConversationMessage(
                            session_id=session_id,
                            role="tool",
                            content=json.dumps(tool_result["result"]),
                            tool_calls=json.dumps([{
                                "id": tool_result["tool_call_id"],
                                "function": tool_result["function"]
                            }])
                        )
                        session.add(tool_msg_record)
                    
                    if tool_results:
                        await session.commit()
                    
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
    """
    Show product details function endpoint.
    
    This endpoint gets detailed product information with optional recommendations.
    Validates product ID against recent search context to prevent AI hallucination.
    """
    try:
        product_id = request.get("product_id", "")
        include_recommendations = request.get("include_recommendations", True)
        session_id = request.get("session_id", "")
        
        if not product_id:
            raise HTTPException(status_code=400, detail="Product ID is required")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Validate product ID against search context (prevent AI hallucination)
        validation = await context_manager.validate_product_id(
            session_id=session_id,
            product_id=product_id,
            session=session
        )
        
        # Get product details
        product = await product_service.get_product_by_id(
            product_id=product_id,
            session=session
        )
        
        if not product:
            # Product doesn't exist - provide suggestions if available
            return {
                "success": False,
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "message": f"Product with ID '{product_id}' was not found",
                    "details": {
                        "product_id": product_id,
                        "suggestions": validation.get("suggestions", []),
                        "recent_searches": validation.get("recent_searches", [])
                    }
                }
            }
        
        # Get recommendations if requested
        recommendations = []
        if include_recommendations:
            rec_products = await product_service.get_recommendations(
                based_on_product_id=product_id,
                limit=5,
                session=session
            )
            recommendations = [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "image_url": p.image_url,
                    "rating": p.rating,
                    "category": p.category
                }
                for p in rec_products
            ]
        
        # Format product details
        product_details = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "long_description": product.long_description or product.description,
            "price": product.price,
            "category": product.category,
            "image_url": product.image_url,
            "additional_images": product.additional_images or [],
            "in_stock": product.in_stock,
            "stock_quantity": product.stock_quantity,
            "rating": product.rating,
            "reviews_count": product.reviews_count,
            "specifications": product.specifications or {},
            "features": product.features or []
        }
        
        return {
            "success": True,
            "data": {
                "product": product_details,
                "recommendations": recommendations
            },
            "validation": {
                "product_exists": True,
                "in_recent_search": validation.get("valid", False),
                "context_valid": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting product details: {str(e)}")


@app.post("/api/functions/add_to_cart")
async def add_to_cart_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Add product to cart function endpoint.
    
    This endpoint adds a product to the user's cart with inventory validation.
    Checks stock availability and updates cart totals.
    """
    try:
        from models import CartItem
        from sqlmodel import select
        
        product_id = request.get("product_id", "")
        quantity = request.get("quantity", 1)
        session_id = request.get("session_id", "")
        
        if not product_id:
            raise HTTPException(status_code=400, detail="Product ID is required")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        if quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")
        
        # Get product to check stock and price
        product = await product_service.get_product_by_id(
            product_id=product_id,
            session=session
        )
        
        if not product:
            return {
                "success": False,
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "message": f"Product with ID '{product_id}' was not found"
                }
            }
        
        # Check stock availability
        if not product.in_stock:
            return {
                "success": False,
                "error": {
                    "code": "OUT_OF_STOCK",
                    "message": f"Product '{product.name}' is currently out of stock"
                }
            }
        
        if product.stock_quantity < quantity:
            return {
                "success": False,
                "error": {
                    "code": "INSUFFICIENT_STOCK",
                    "message": f"Only {product.stock_quantity} units available",
                    "details": {
                        "requested": quantity,
                        "available": product.stock_quantity
                    }
                }
            }
        
        # Check if item already in cart
        statement = select(CartItem).where(
            CartItem.session_id == session_id,
            CartItem.product_id == product_id
        )
        result = await session.execute(statement)
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            # Update existing cart item
            existing_item.quantity += quantity
            existing_item.total_price = existing_item.quantity * product.price
            session.add(existing_item)
            await session.commit()
            await session.refresh(existing_item)
            cart_item = existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price,
                total_price=quantity * product.price
            )
            session.add(cart_item)
            await session.commit()
            await session.refresh(cart_item)
        
        # Calculate cart summary
        statement = select(CartItem).where(CartItem.session_id == session_id)
        result = await session.execute(statement)
        all_cart_items = result.scalars().all()
        
        total_items = sum(item.quantity for item in all_cart_items)
        subtotal = sum(item.total_price for item in all_cart_items)
        estimated_tax = round(subtotal * 0.1, 2)  # 10% tax
        estimated_total = round(subtotal + estimated_tax, 2)
        
        return {
            "success": True,
            "data": {
                "cart_item": {
                    "id": cart_item.id,
                    "product_id": cart_item.product_id,
                    "product_name": product.name,
                    "quantity": cart_item.quantity,
                    "unit_price": cart_item.unit_price,
                    "total_price": cart_item.total_price,
                    "added_at": cart_item.added_at.isoformat()
                },
                "cart_summary": {
                    "total_items": total_items,
                    "total_products": len(all_cart_items),
                    "subtotal": subtotal,
                    "estimated_tax": estimated_tax,
                    "estimated_total": estimated_total
                }
            },
            "validation": {
                "product_exists": True,
                "sufficient_stock": True,
                "valid_quantity": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to cart: {str(e)}")


@app.post("/api/functions/remove_from_cart")
async def remove_from_cart_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Remove product from cart function endpoint.
    
    Can remove specific quantity or remove item entirely.
    """
    try:
        from models import CartItem
        from sqlmodel import select
        
        product_id = request.get("product_id", "")
        quantity = request.get("quantity")  # Optional - if None, remove entire item
        session_id = request.get("session_id", "")
        
        if not product_id:
            raise HTTPException(status_code=400, detail="Product ID is required")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Find cart item
        statement = select(CartItem).where(
            CartItem.session_id == session_id,
            CartItem.product_id == product_id
        )
        result = await session.execute(statement)
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return {
                "success": False,
                "error": {
                    "code": "ITEM_NOT_IN_CART",
                    "message": f"Product '{product_id}' is not in your cart"
                }
            }
        
        # Determine action
        if quantity is None or quantity >= cart_item.quantity:
            # Remove item entirely
            await session.delete(cart_item)
            await session.commit()
            removed_quantity = cart_item.quantity
            action = "removed"
        else:
            # Reduce quantity
            cart_item.quantity -= quantity
            cart_item.total_price = cart_item.quantity * cart_item.unit_price
            session.add(cart_item)
            await session.commit()
            await session.refresh(cart_item)
            removed_quantity = quantity
            action = "reduced"
        
        # Get updated cart summary
        statement = select(CartItem).where(CartItem.session_id == session_id)
        result = await session.execute(statement)
        all_cart_items = result.scalars().all()
        
        total_items = sum(item.quantity for item in all_cart_items)
        subtotal = sum(item.total_price for item in all_cart_items)
        estimated_tax = round(subtotal * 0.1, 2)
        estimated_total = round(subtotal + estimated_tax, 2)
        
        return {
            "success": True,
            "data": {
                "action": action,
                "removed_quantity": removed_quantity,
                "cart_summary": {
                    "total_items": total_items,
                    "total_products": len(all_cart_items),
                    "subtotal": subtotal,
                    "estimated_tax": estimated_tax,
                    "estimated_total": estimated_total
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing from cart: {str(e)}")


@app.get("/api/cart/{session_id}")
async def get_cart(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get current cart contents for a session.
    """
    try:
        from models import CartItem
        from sqlmodel import select
        
        # Get all cart items
        statement = select(CartItem).where(CartItem.session_id == session_id)
        result = await session.execute(statement)
        cart_items = result.scalars().all()
        
        # Get product details for each item
        items_with_details = []
        for item in cart_items:
            product = await product_service.get_product_by_id(item.product_id, session)
            if product:
                items_with_details.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": product.name,
                    "product_image": product.image_url,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                    "added_at": item.added_at.isoformat()
                })
        
        # Calculate totals
        total_items = sum(item.quantity for item in cart_items)
        subtotal = sum(item.total_price for item in cart_items)
        estimated_tax = round(subtotal * 0.1, 2)
        estimated_total = round(subtotal + estimated_tax, 2)
        
        return {
            "success": True,
            "items": items_with_details,
            "summary": {
                "total_items": total_items,
                "total_products": len(items_with_details),
                "subtotal": float(subtotal),
                "estimated_tax": float(estimated_tax),
                "estimated_total": float(estimated_total)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cart: {str(e)}")


@app.post("/api/functions/get_recommendations")
async def get_recommendations_endpoint(
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Get product recommendations function endpoint.
    
    This endpoint returns product recommendations based on a product ID or category.
    Uses collaborative filtering approach (same category products).
    """
    try:
        based_on = request.get("based_on", "")  # Product ID or category
        recommendation_type = request.get("recommendation_type", "similar")
        max_results = request.get("max_results", 5)
        session_id = request.get("session_id", "")
        
        if not based_on:
            raise HTTPException(status_code=400, detail="'based_on' parameter is required (product ID or category)")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        if max_results < 1 or max_results > 20:
            raise HTTPException(status_code=400, detail="max_results must be between 1 and 20")
        
        # Check if based_on is a product ID or category
        product = await product_service.get_product_by_id(
            product_id=based_on,
            session=session
        )
        
        if product:
            # based_on is a product ID
            recommendations = await product_service.get_recommendations(
                based_on_product_id=product.id,
                limit=max_results,
                session=session
            )
            
            recommendation_context = {
                "based_on_product": product.name,
                "based_on_category": product.category,
                "algorithm": "collaborative_filtering",
                "factors": ["category", "price_range", "ratings"]
            }
        else:
            # based_on might be a category - search by category
            from models import ProductCategory
            
            try:
                # Try to match as category
                category = ProductCategory(based_on.lower())
                recommendations = await product_service.search_products(
                    query="",
                    category=category,
                    limit=max_results,
                    session=session
                )
                
                recommendation_context = {
                    "based_on_category": based_on,
                    "algorithm": "category_based",
                    "factors": ["category", "popularity", "ratings"]
                }
            except ValueError:
                # Not a valid category either
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_REFERENCE",
                        "message": f"'{based_on}' is neither a valid product ID nor a category",
                        "details": {
                            "valid_categories": ["electronics", "clothing", "home", "books", "sports", "beauty"]
                        }
                    }
                }
        
        # Format recommendations
        recommendations_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "category": p.category,
                "image_url": p.image_url,
                "rating": p.rating,
                "reviews_count": p.reviews_count,
                "in_stock": p.in_stock,
                "similarity_score": 0.85 if product and p.category == product.category else 0.75,
                "reason": f"Similar {'features and ' if product else ''}category" if product else "Popular in category"
            }
            for p in recommendations
        ]
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations_data,
                "recommendation_context": recommendation_context
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )