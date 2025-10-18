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
    """OpenAI-based AI agent implementation with native function calling."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

        self.model = os.getenv("AI_MODEL", "gpt-4o")
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
    async def stream_response(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response from OpenAI with function calling support.
        
        Yields dictionaries with keys:
        - type: "text" | "tool_call" | "error"
        - content: the actual content (text string or tool call dict)
        """
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build messages with context if available
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                }
            ]
            
            # Add context if available
            if context:
                context_str = f"User context: {json.dumps(context)}"
                messages.append({
                    "role": "system",
                    "content": context_str
                })
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": self._get_function_definitions(), 
                "tool_choice": "auto",  # Let AI decide when to call functions
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            try:
                # Track tool calls across streaming chunks
                current_tool_calls = {}
                
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
                                    
                                    # Handle text content
                                    content = delta.get("content")
                                    if content:
                                        yield {
                                            "type": "text",
                                            "content": content
                                        }
                                    
                                    # Handle tool calls
                                    tool_calls = delta.get("tool_calls")
                                    if tool_calls:
                                        for tool_call in tool_calls:
                                            idx = tool_call.get("index", 0)
                                            
                                            # Initialize tool call if new
                                            if idx not in current_tool_calls:
                                                current_tool_calls[idx] = {
                                                    "id": tool_call.get("id", ""),
                                                    "type": tool_call.get("type", "function"),
                                                    "function": {
                                                        "name": "",
                                                        "arguments": ""
                                                    }
                                                }
                                            
                                            # Update tool call data
                                            if "id" in tool_call:
                                                current_tool_calls[idx]["id"] = tool_call["id"]
                                            
                                            if "function" in tool_call:
                                                func = tool_call["function"]
                                                if "name" in func:
                                                    current_tool_calls[idx]["function"]["name"] = func["name"]
                                                if "arguments" in func:
                                                    current_tool_calls[idx]["function"]["arguments"] += func["arguments"]
                                        
                            except json.JSONDecodeError:
                                continue
                
                # Yield completed tool calls
                for tool_call in current_tool_calls.values():
                    if tool_call["function"]["name"]:  # Only if we have a function name
                        try:
                            arguments = json.loads(tool_call["function"]["arguments"])
                            yield {
                                "type": "tool_call",
                                "content": {
                                    "id": tool_call["id"],
                                    "function": tool_call["function"]["name"],
                                    "arguments": arguments
                                }
                            }
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse tool call arguments: {e}")
                            print(f"Arguments string: {tool_call['function']['arguments']}")
                                
            except httpx.HTTPStatusError as e:
                error_msg = f"OpenAI API error: {e.response.status_code}"
                if e.response.status_code == 401:
                    error_msg = "Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env file."
                elif e.response.status_code == 429:
                    error_msg = "OpenAI rate limit exceeded. Please try again later."
                yield {
                    "type": "error",
                    "content": error_msg
                }
                
            except Exception as e:
                yield {
                    "type": "error",
                    "content": f"Error communicating with OpenAI: {str(e)}"
                }
    
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
        """Get OpenAI tool definitions for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Search for products in the catalog based on keywords, category, or other criteria. Use this when the user wants to find or browse products.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (product name, keywords, features)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Product category to filter by",
                                "enum": ["electronics", "clothing", "home", "books", "sports", "beauty"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "show_product_details",
                    "description": "Get comprehensive details about a specific product including specifications, features, ratings, and recommendations. Use when the user asks for more information about a particular product.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "The unique product ID (e.g., 'prod_001')"
                            },
                            "include_recommendations": {
                                "type": "boolean",
                                "description": "Whether to include similar product recommendations",
                                "default": True
                            }
                        },
                        "required": ["product_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_to_cart",
                    "description": "Add a product to the user's shopping cart. Checks inventory and returns cart summary with totals.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "The unique product ID to add"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity to add to cart",
                                "default": 1,
                                "minimum": 1
                            }
                        },
                        "required": ["product_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recommendations",
                    "description": "Get product recommendations based on a product ID, category, or user preferences. Returns similar or related products.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "based_on": {
                                "type": "string",
                                "description": "Product ID or category to base recommendations on (e.g., 'prod_001' or 'electronics')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of recommendations",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["based_on"]
                    }
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