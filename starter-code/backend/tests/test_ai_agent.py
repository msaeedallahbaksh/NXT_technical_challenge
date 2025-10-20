"""
Tests for AI Agent implementations (OpenAI, Anthropic).

This module tests the production AI agent layer that handles streaming 
responses and function calling integration with real AI providers.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from ai_agent import OpenAIAgent, AnthropicAgent


class TestOpenAIAgent:
    """Tests for OpenAIAgent."""
    
    def test_openai_agent_requires_api_key(self):
        """Test OpenAI agent requires API key."""
        import os
        old_key = os.environ.get("OPENAI_API_KEY")
        
        # Remove API key
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            OpenAIAgent()
        
        # Restore key
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
    
    def test_openai_agent_initialization_with_key(self):
        """Test OpenAI agent initializes with API key."""
        import os
        os.environ["OPENAI_API_KEY"] = "test_key"
        
        agent = OpenAIAgent()
        assert agent.api_key == "test_key"
        assert agent.model is not None
    
    def test_openai_agent_get_system_prompt(self):
        """Test OpenAI agent system prompt generation."""
        import os
        os.environ["OPENAI_API_KEY"] = "test_key"
        agent = OpenAIAgent()
        
        prompt = agent._get_system_prompt()
        assert len(prompt) > 0
        assert "shopping assistant" in prompt.lower()
    
    def test_openai_agent_system_prompt_with_context(self):
        """Test system prompt includes context."""
        import os
        os.environ["OPENAI_API_KEY"] = "test_key"
        agent = OpenAIAgent()
        
        context = {
            "cart_items": ["prod_1", "prod_2"],
            "recent_searches": ["headphones", "laptops"]
        }
        
        prompt = agent._get_system_prompt(context)
        assert "cart" in prompt.lower() or "2" in prompt
    
    def test_openai_agent_function_definitions(self):
        """Test OpenAI agent has all required function definitions."""
        import os
        os.environ["OPENAI_API_KEY"] = "test_key"
        agent = OpenAIAgent()
        
        functions = agent._get_function_definitions()
        
        assert len(functions) == 4
        function_names = [f["function"]["name"] for f in functions]
        assert "search_products" in function_names
        assert "show_product_details" in function_names
        assert "add_to_cart" in function_names
        assert "get_recommendations" in function_names


class TestAnthropicAgent:
    """Tests for AnthropicAgent."""
    
    def test_anthropic_agent_requires_api_key(self):
        """Test Anthropic agent requires API key."""
        import os
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # Remove API key
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AnthropicAgent()
        
        # Restore key
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key
    
    def test_anthropic_agent_initialization_with_key(self):
        """Test Anthropic agent initializes with API key."""
        import os
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        
        agent = AnthropicAgent()
        assert agent.api_key == "test_key"
        assert agent.model is not None
    
    def test_anthropic_agent_get_system_prompt(self):
        """Test Anthropic agent system prompt generation."""
        import os
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        agent = AnthropicAgent()
        
        prompt = agent._get_system_prompt()
        assert len(prompt) > 0
        assert "shopping assistant" in prompt.lower()
    
    def test_anthropic_agent_claude_tool_definitions(self):
        """Test Anthropic agent has Claude-format tool definitions."""
        import os
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        agent = AnthropicAgent()
        
        tools = agent._get_claude_tool_definitions()
        
        assert len(tools) == 4
        tool_names = [t["name"] for t in tools]
        assert "search_products" in tool_names
        assert "show_product_details" in tool_names
        assert "add_to_cart" in tool_names
        assert "get_recommendations" in tool_names
        
        # Verify Claude-specific format
        for tool in tools:
            assert "input_schema" in tool


# Mock AI tests removed - production code uses only real AI providers (OpenAI/Anthropic)

