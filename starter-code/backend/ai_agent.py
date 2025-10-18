"""
AI Agent implementation for the Product Discovery Assistant.

This module provides both real AI integration (OpenAI/Anthropic) and mock
implementations for development and testing.
"""

import os
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional

import httpx


class AIAgent(ABC):
    """Abstract base class for AI agents."""
    
    @abstractmethod
    async def stream_response(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream AI response chunks."""
        pass
    
    @abstractmethod
    async def execute_function(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute function call."""
        pass


class OpenAIAgent(AIAgent):
    """OpenAI-based AI agent implementation."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
    
    async def stream_response(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": message
                    }
                ],
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            try:
                async with client.stream("POST", f"{self.base_url}/chat/completions", 
                                        headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    
                                    if content:
                                        yield content
                                        
                            except json.JSONDecodeError:
                                continue
                                
            except httpx.HTTPStatusError as e:
                error_msg = f"OpenAI API error: {e.response.status_code}"
                if e.response.status_code == 401:
                    error_msg = "Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env file."
                elif e.response.status_code == 429:
                    error_msg = "OpenAI rate limit exceeded. Please try again later."
                yield f"Error: {error_msg}"
                
            except Exception as e:
                yield f"Error communicating with OpenAI: {str(e)}"
    
    async def execute_function(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute function call (delegated to backend endpoints)."""
        # Function execution happens in the main.py endpoints
        # This is just a placeholder for the agent interface
        return {
            "status": "delegated",
            "function": function_name,
            "parameters": parameters
        }
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI agent."""
        return """
        You are a helpful AI shopping assistant. You can help users:
        - Search for products
        - Get detailed product information
        - Add items to their cart
        - Get product recommendations
        
        Always use function calls when appropriate and be helpful and friendly.
        """
    
    def _get_function_definitions(self) -> list:
        """Get OpenAI function definitions."""
        return [
            {
                "name": "search_products",
                "description": "Search for products based on user query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                        "limit": {"type": "integer"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "show_product_details",
                "description": "Show detailed information about a product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string"},
                        "include_recommendations": {"type": "boolean"}
                    },
                    "required": ["product_id"]
                }
            }
        ]


class MockAIAgent(AIAgent):
    """Mock AI agent for development and testing."""
    
    def __init__(self):
        self.responses = {
            "search": [
                "I'll help you search for products! Let me look that up for you.",
                " I found some great options that match your query.",
                " Here are the search results I found."
            ],
            "details": [
                "Let me get the detailed information for that product.",
                " Here are all the details and specifications you requested.",
                " I've also included some related recommendations you might like."
            ],
            "cart": [
                "Great choice! I'll add that item to your cart.",
                " The item has been successfully added.",
                " Your cart has been updated with the new item."
            ],
            "recommendations": [
                "Based on your interests, I have some great recommendations!",
                " These products are similar to what you're looking for.",
                " You might also be interested in these related items."
            ]
        }
    
    async def stream_response(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream mock AI response."""
        
        # Determine response type based on message
        response_type = "search"  # default
        if "detail" in message.lower():
            response_type = "details"
        elif "cart" in message.lower() or "add" in message.lower():
            response_type = "cart"
        elif "recommend" in message.lower():
            response_type = "recommendations"
        
        # Stream the response
        response_chunks = self.responses.get(response_type, self.responses["search"])
        
        for chunk in response_chunks:
            yield chunk
            await asyncio.sleep(0.2)  # Simulate realistic streaming delay
    
    async def execute_function(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute mock function call."""
        
        # Simulate function execution delay
        await asyncio.sleep(0.5)
        
        if function_name == "search_products":
            return {
                "products": [
                    {
                        "id": "prod_123",
                        "name": "Sample Product 1",
                        "description": "A great sample product",
                        "price": 99.99,
                        "category": "electronics",
                        "image_url": "https://via.placeholder.com/300x300",
                        "in_stock": True,
                        "rating": 4.5,
                        "reviews_count": 127
                    },
                    {
                        "id": "prod_124", 
                        "name": "Sample Product 2",
                        "description": "Another excellent product",
                        "price": 149.99,
                        "category": "electronics",
                        "image_url": "https://via.placeholder.com/300x300",
                        "in_stock": True,
                        "rating": 4.7,
                        "reviews_count": 89
                    }
                ],
                "total_results": 2,
                "search_context": {
                    "query": parameters.get("query", ""),
                    "category": parameters.get("category"),
                    "results_cached": True
                }
            }
        
        elif function_name == "show_product_details":
            return {
                "product": {
                    "id": parameters.get("product_id", "prod_123"),
                    "name": "Sample Product Details",
                    "description": "Detailed product information",
                    "long_description": "This is a comprehensive description of the product with all its features and benefits.",
                    "price": 99.99,
                    "category": "electronics",
                    "image_url": "https://via.placeholder.com/300x300",
                    "in_stock": True,
                    "stock_quantity": 15,
                    "rating": 4.5,
                    "reviews_count": 127,
                    "specifications": {
                        "brand": "Sample Brand",
                        "model": "SB-123",
                        "warranty": "1 year"
                    },
                    "features": [
                        "High quality materials",
                        "Excellent performance", 
                        "Great value for money"
                    ]
                },
                "recommendations": [
                    {
                        "id": "prod_125",
                        "name": "Related Product",
                        "price": 79.99,
                        "image_url": "https://via.placeholder.com/300x300"
                    }
                ]
            }
        
        elif function_name == "add_to_cart":
            return {
                "cart_item": {
                    "id": 1,
                    "product_id": parameters.get("product_id", "prod_123"),
                    "product_name": "Sample Product",
                    "quantity": parameters.get("quantity", 1),
                    "unit_price": 99.99,
                    "total_price": 99.99 * parameters.get("quantity", 1)
                },
                "cart_summary": {
                    "total_items": parameters.get("quantity", 1),
                    "total_products": 1,
                    "subtotal": 99.99 * parameters.get("quantity", 1),
                    "estimated_tax": 9.99,
                    "estimated_total": 109.98
                }
            }
        
        elif function_name == "get_recommendations":
            return {
                "recommendations": [
                    {
                        "id": "prod_126",
                        "name": "Recommended Product 1",
                        "price": 89.99,
                        "image_url": "https://via.placeholder.com/300x300",
                        "similarity_score": 0.85,
                        "reason": "Similar features and category"
                    },
                    {
                        "id": "prod_127",
                        "name": "Recommended Product 2", 
                        "price": 119.99,
                        "image_url": "https://via.placeholder.com/300x300",
                        "similarity_score": 0.78,
                        "reason": "Customers also bought this item"
                    }
                ],
                "recommendation_context": {
                    "based_on": parameters.get("based_on", ""),
                    "algorithm": "collaborative_filtering",
                    "factors": ["category", "price_range", "ratings"]
                }
            }
        
        else:
            return {
                "error": f"Unknown function: {function_name}",
                "parameters": parameters
            }


# Factory function to create AI agent
def create_ai_agent() -> AIAgent:
    """Create AI agent based on configuration."""
    provider = os.getenv("AI_PROVIDER", "simulate").lower()
    
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return OpenAIAgent()
    elif provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        # TODO: Implement AnthropicAgent
        raise NotImplementedError("Anthropic agent not yet implemented")
    else:
        return MockAIAgent()