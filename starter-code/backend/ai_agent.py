"""
AI Agent implementation for the Product Discovery Assistant.

This module provides both real AI integration (OpenAI/Anthropic) and mock
implementations for development and testing.
"""

import os
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional, List

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
        session_id: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response from OpenAI with function calling support.
        
        Args:
            message: Current user message
            context: Session context (cart, search results)
            session_id: Session identifier
            conversation_history: Previous messages in conversation
        
        Yields dictionaries with keys:
        - type: "text" | "tool_call" | "error"
        - content: the actual content (text string or tool call dict)
        """
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build messages array starting with system prompt
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(context)
                }
            ]
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
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
                        except json.JSONDecodeError:
                            pass
                                
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
    
    def _get_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get system prompt for the AI agent with current context."""
        base_prompt = """You are a friendly AI shopping assistant helping customers find and purchase products.

CAPABILITIES:
- Search for products by name, category, or features
- Show detailed product information
- Add items to shopping cart
- Provide personalized recommendations

IMPORTANT CONVERSATION RULES:
1. ALWAYS provide a friendly text response alongside tool calls - never just execute functions silently
2. Narrate what you're doing: "Let me search for that...", "I found some great options!", "I'll add that to your cart!"
3. Be conversational and enthusiastic about helping
4. After tool results, comment on what was found or done

EXAMPLES:
User: "search for headphones"
You: "Let me find some great headphones for you! 🎧" [then call search_products]

User: "add the first one to my cart"  
You: "Perfect choice! I'll add that to your cart right away! 🛒" [then call add_to_cart]

User: "show me product details"
You: "Let me get all the details for you! ✨" [then call show_product_details]

Always be helpful, enthusiastic, and conversational!"""
        
        # Add context information if available
        if context:
            context_parts = []
            
            # Add cart information
            if context.get("cart_items"):
                cart_count = len(context["cart_items"])
                context_parts.append(f"- User currently has {cart_count} item(s) in their cart")
            
            # Add recent search context
            if context.get("recent_searches"):
                searches = context["recent_searches"][:3]  # Last 3 searches
                context_parts.append(f"- Recent searches: {', '.join(searches)}")
            
            # Add recently viewed products
            if context.get("viewed_products"):
                products = context["viewed_products"][:5]  # Last 5 viewed
                context_parts.append(f"- Recently viewed products: {', '.join(products)}")
            
            if context_parts:
                base_prompt += "\n\nCURRENT CONTEXT:\n" + "\n".join(context_parts)
        
        return base_prompt
    
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


class AnthropicAgent(AIAgent):
    """Anthropic Claude-based AI agent implementation with native function calling."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022")
        self.base_url = "https://api.anthropic.com/v1"
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
    
    async def stream_response(
        self, 
        message: str, 
        context: Dict[str, Any],
        session_id: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response from Claude with function calling support.
        
        Args:
            message: Current user message
            context: Session context (cart, search results)
            session_id: Session identifier
            conversation_history: Previous messages in conversation
        
        Yields dictionaries with keys:
        - type: "text" | "tool_call" | "error"
        - content: the actual content (text string or tool call dict)
        """
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                # Remove beta header per API error; tools are supported natively on Messages API
                "Content-Type": "application/json"
            }
            
            # Claude separates system from messages and has a different format for tool results
            messages = []
            
            # Add conversation history if available (convert OpenAI format to Claude format)
            if conversation_history:
                i = 0
                while i < len(conversation_history):
                    msg = conversation_history[i]
                    role = msg.get("role")
                    
                    # Skip system messages (handled separately)
                    if role == "system":
                        i += 1
                        continue
                    
                    # Handle assistant messages with tool calls
                    if role == "assistant":
                        tool_calls = msg.get("tool_calls")
                        content = msg.get("content", "")
                        
                        # Build content array for Claude format
                        content_blocks = []
                        if content:
                            content_blocks.append({"type": "text", "text": content})
                        
                        # Add tool_use blocks if present
                        if tool_calls:
                            for tc in tool_calls:
                                # Parse arguments if they're a JSON string (from OpenAI format)
                                arguments = tc["function"]["arguments"]
                                if isinstance(arguments, str):
                                        try:
                                            arguments = json.loads(arguments)
                                        except json.JSONDecodeError:
                                            arguments = {}
                                
                                content_blocks.append({
                                    "type": "tool_use",
                                    "id": tc["id"],
                                    "name": tc["function"]["name"],
                                    "input": arguments  # Must be dict, not string
                                })
                        
                        # Only add assistant message if there's content
                        if content_blocks:
                            messages.append({
                                "role": "assistant",
                                "content": content_blocks
                            })
                    
                    # Handle tool results - need to collect all following tool messages and bundle into user message
                    elif role == "tool":
                        tool_results = []
                        
                        # Collect all consecutive tool messages
                        while i < len(conversation_history) and conversation_history[i].get("role") == "tool":
                            tool_msg = conversation_history[i]
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_msg.get("tool_call_id"),
                                "content": tool_msg.get("content")
                            })
                            i += 1
                        
                        # Add as user message with tool_result blocks
                        messages.append({
                            "role": "user",
                            "content": tool_results
                        })
                        continue  # Don't increment i again
                    
                    # Handle regular user messages
                    elif role == "user":
                        # Always send user content as text blocks
                        user_text = msg.get("content", "")
                        messages.append({
                            "role": "user",
                            "content": [{"type": "text", "text": user_text}]
                        })
                    
                    i += 1
            
            # Add current user message
            # If the last message is a user message (e.g., from tool results),
            # append to it instead of creating a new user message
            if messages and messages[-1]["role"] == "user":
                # Append text block to existing user message
                if isinstance(messages[-1]["content"], list):
                    messages[-1]["content"].append({"type": "text", "text": message})
                else:
                    # Shouldn't happen, but handle just in case
                    messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": message}]
                    })
            else:
                # Create new user message
                messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": message}]
                })
            
            payload = {
                "model": self.model,
                "max_tokens": 1500,
                "temperature": 0.7,
                "system": self._get_system_prompt(context),
                "messages": messages,
                "tools": self._get_claude_tool_definitions(),
                "stream": True,
                "tool_choice": {"type": "auto"}
            }
            
            
            try:
                # Track accumulated text and tool uses
                current_text = ""
                # Map content block index -> tool_use state
                tool_uses_by_index: Dict[int, Dict[str, Any]] = {}
                
                async with client.stream("POST", f"{self.base_url}/messages", 
                                        headers=headers, json=payload) as response:
                    # Check status before consuming stream
                    if response.status_code != 200:
                        response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            # Handle tool use blocks
                            if event_type == "content_block_start":
                                content_block = data.get("content_block", {})
                                if content_block.get("type") == "tool_use":
                                    tool_name = content_block.get("name")
                                    tool_id = content_block.get("id")
                                    tool_input = content_block.get("input", {})
                                    block_index = data.get("index")
                                    
                                    # Initialize state for this block index
                                    if block_index is not None:
                                        tool_uses_by_index[block_index] = {
                                            "id": tool_id,
                                            "name": tool_name,
                                            "input": tool_input if tool_input and tool_input != {} else ""
                                        }
                                    else:
                                        # Fallback to index -1 if index missing
                                        tool_uses_by_index[-1] = {
                                            "id": tool_id,
                                            "name": tool_name,
                                            "input": tool_input if tool_input and tool_input != {} else ""
                                        }
                            
                            # Handle content block deltas (text AND tool inputs)
                            elif event_type == "content_block_delta":
                                delta = data.get("delta", {})
                                delta_type = delta.get("type")
                                block_index = data.get("index")
                                
                                # Handle text deltas
                                if delta_type == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        current_text += text
                                        yield {
                                            "type": "text",
                                            "content": text
                                        }
                                
                                # Handle tool input deltas (streaming JSON)
                                elif delta_type == "input_json_delta":
                                    state = tool_uses_by_index.get(block_index) or tool_uses_by_index.get(-1)
                                    if state is not None:
                                        partial_json = delta.get("partial_json", "")
                                        if isinstance(partial_json, str):
                                            if not isinstance(state["input"], str):
                                                state["input"] = ""
                                            state["input"] += partial_json
                            
                            # Handle completed blocks
                            elif event_type == "content_block_stop":
                                block_index = data.get("index")
                                state = tool_uses_by_index.get(block_index) or tool_uses_by_index.get(-1)
                                if state is not None:
                                    # Parse accumulated string input to dict
                                    if isinstance(state["input"], str):
                                        if state["input"]:
                                            try:
                                                state["input"] = json.loads(state["input"])
                                            except json.JSONDecodeError:
                                                state["input"] = {}
                                        else:
                                            state["input"] = {}
                                    
                                    # Yield tool call
                                    if isinstance(state["input"], dict):
                                        yield {
                                            "type": "tool_call",
                                            "content": {
                                                "id": state["id"],
                                                "function": state["name"],
                                                "arguments": state["input"]
                                            }
                                        }
                                    
                                    # Clean up this block index
                                    if block_index in tool_uses_by_index:
                                        del tool_uses_by_index[block_index]
                                        
                        except json.JSONDecodeError:
                            continue
                                
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                detail = ""
                try:
                    error_detail = e.response.json()
                    detail = error_detail.get("error", {}).get("message", "") or json.dumps(error_detail)[:500]
                except Exception:
                    try:
                        detail = (await e.response.aread()).decode(errors="ignore")[:500]
                    except Exception:
                        detail = ""
                
                error_msg = f"Claude API error: {status}"
                
                if status == 401:
                    error_msg = "Invalid Anthropic API key. Please check your ANTHROPIC_API_KEY in .env file."
                elif status == 429:
                    error_msg = "Claude rate limit exceeded. Please try again later."
                elif status == 400:
                    error_msg = f"Bad request to Claude: {detail if detail else 'Invalid request format'}"
                
                yield {
                    "type": "error",
                    "content": error_msg
                }
                
            except Exception as e:
                yield {
                    "type": "error",
                    "content": f"Error communicating with Claude: {str(e)}"
                }
    
    async def execute_function(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute function call (delegated to backend endpoints)."""
        return {
            "status": "delegated",
            "function": function_name,
            "parameters": parameters
        }
    
    def _get_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get system prompt for the AI agent with current context."""
        base_prompt = """You are a friendly AI shopping assistant helping customers find and purchase products.

CAPABILITIES:
- Search for products by name, category, or features
- Show detailed product information
- Add items to shopping cart
- Provide personalized recommendations

IMPORTANT CONVERSATION RULES:
1. ALWAYS provide a friendly text response alongside tool calls - never just execute functions silently
2. Narrate what you're doing: "Let me search for that...", "I found some great options!", "I'll add that to your cart!"
3. Be conversational and enthusiastic about helping
4. After tool results, comment on what was found or done

EXAMPLES:
User: "search for headphones"
You: "Let me find some great headphones for you! 🎧" [then call search_products]

User: "add the first one to my cart"  
You: "Perfect choice! I'll add that to your cart right away! 🛒" [then call add_to_cart]

User: "show me product details"
You: "Let me get all the details for you! ✨" [then call show_product_details]

Always be helpful, enthusiastic, and conversational!"""
        
        # Add context information if available
        if context:
            context_parts = []
            
            if context.get("cart_items"):
                cart_count = len(context["cart_items"])
                context_parts.append(f"- User currently has {cart_count} item(s) in their cart")
            
            if context.get("recent_searches"):
                searches = context["recent_searches"][:3]
                context_parts.append(f"- Recent searches: {', '.join(searches)}")
            
            if context.get("viewed_products"):
                products = context["viewed_products"][:5]
                context_parts.append(f"- Recently viewed products: {', '.join(products)}")
            
            if context_parts:
                base_prompt += "\n\nCURRENT CONTEXT:\n" + "\n".join(context_parts)
        
        return base_prompt
    
    def _get_claude_tool_definitions(self) -> list:
        """Get Claude tool definitions for function calling."""
        return [
            {
                "name": "search_products",
                "description": "Search for products in the catalog based on keywords, category, or other criteria. Use this when the user wants to find or browse products.",
                "input_schema": {
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
            },
            {
                "name": "show_product_details",
                "description": "Get comprehensive details about a specific product including specifications, features, ratings, and recommendations. Use when the user asks for more information about a particular product.",
                "input_schema": {
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
            },
            {
                "name": "add_to_cart",
                "description": "Add a product to the user's shopping cart. Checks inventory and returns cart summary with totals.",
                "input_schema": {
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
            },
            {
                "name": "get_recommendations",
                "description": "Get product recommendations based on a product ID, category, or user preferences. Returns similar or related products.",
                "input_schema": {
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
        return AnthropicAgent()
    else:
        return MockAIAgent()