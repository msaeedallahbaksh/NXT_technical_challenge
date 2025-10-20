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

SEARCH FUNCTION USAGE:
- When user wants to browse a category (e.g., "show me electronics", "what clothing do you have"), use only the category parameter, leave query empty or omit it
- When user searches by name/keyword (e.g., "wireless headphones"), use the query parameter
- You can combine both: query="wireless" AND category="electronics"

EXAMPLES:
User: "show me electronics" or "what electronics do you have"
You: "Let me browse our electronics section for you! 📱💻" [call search_products with category="electronics", no query]

User: "search for headphones"
You: "Let me find some great headphones for you! 🎧" [call search_products with query="headphones"]

User: "wireless headphones in electronics"  
You: "Let me search for wireless headphones in our electronics! 🎧" [call search_products with query="wireless headphones", category="electronics"]

User: "add the first one to my cart"  
You: "Perfect choice! I'll add that to your cart right away! 🛒" [call add_to_cart]

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
                    "description": "Search for products in the catalog. Can search by keywords, browse by category, or both. Use this when the user wants to find or browse products.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for product name, keywords, or features. Optional - leave empty when browsing by category only."
                            },
                            "category": {
                                "type": "string",
                                "description": "Product category to filter by. Use this when the user wants to browse or filter by category (e.g., 'show me electronics', 'clothing items', 'books section').",
                                "enum": ["electronics", "clothing", "home", "books", "sports", "beauty"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10
                            }
                        },
                        "required": []
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

SEARCH FUNCTION USAGE:
- When user wants to browse a category (e.g., "show me electronics", "what clothing do you have"), use only the category parameter, leave query empty or omit it
- When user searches by name/keyword (e.g., "wireless headphones"), use the query parameter
- You can combine both: query="wireless" AND category="electronics"

EXAMPLES:
User: "show me electronics" or "what electronics do you have"
You: "Let me browse our electronics section for you! 📱💻" [call search_products with category="electronics", no query]

User: "search for headphones"
You: "Let me find some great headphones for you! 🎧" [call search_products with query="headphones"]

User: "wireless headphones in electronics"  
You: "Let me search for wireless headphones in our electronics! 🎧" [call search_products with query="wireless headphones", category="electronics"]

User: "add the first one to my cart"  
You: "Perfect choice! I'll add that to your cart right away! 🛒" [call add_to_cart]

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
                "description": "Search for products in the catalog. Can search by keywords, browse by category, or both. Use this when the user wants to find or browse products.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for product name, keywords, or features. Optional - leave empty when browsing by category only."
                        },
                        "category": {
                            "type": "string",
                            "description": "Product category to filter by. Use this when the user wants to browse or filter by category (e.g., 'show me electronics', 'clothing items', 'books section').",
                            "enum": ["electronics", "clothing", "home", "books", "sports", "beauty"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    },
                    "required": []
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


# No mock agents - production code only uses real AI providers