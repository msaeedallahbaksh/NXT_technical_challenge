"""
Tests for AI Agent implementations (Mock, OpenAI, Anthropic).

This module tests the AI agent layer that handles streaming responses
and function calling integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from ai_agent import MockAIAgent, OpenAIAgent, AnthropicAgent, create_ai_agent


class TestMockAIAgent:
    """Tests for MockAIAgent."""
    
    @pytest.mark.asyncio
    async def test_mock_agent_stream_response(self):
        """Test mock agent streams response chunks."""
        agent = MockAIAgent()
        
        chunks = []
        async for chunk in agent.stream_response(
            message="search for headphones",
            context={},
            session_id="test_session"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_mock_agent_different_response_types(self):
        """Test mock agent provides different responses based on message."""
        agent = MockAIAgent()
        
        # Test search response
        chunks_search = []
        async for chunk in agent.stream_response(
            message="search for laptops",
            context={},
            session_id="test"
        ):
            chunks_search.append(chunk)
        
        # Test cart response
        chunks_cart = []
        async for chunk in agent.stream_response(
            message="add to cart",
            context={},
            session_id="test"
        ):
            chunks_cart.append(chunk)
        
        # Responses should be different
        assert chunks_search != chunks_cart
    
    @pytest.mark.asyncio
    async def test_mock_agent_execute_search_function(self):
        """Test mock agent executes search function."""
        agent = MockAIAgent()
        
        result = await agent.execute_function(
            function_name="search_products",
            parameters={"query": "headphones", "limit": 10},
            session_id="test"
        )
        
        assert "products" in result
        assert len(result["products"]) > 0
        assert "total_results" in result
    
    @pytest.mark.asyncio
    async def test_mock_agent_execute_details_function(self):
        """Test mock agent executes product details function."""
        agent = MockAIAgent()
        
        result = await agent.execute_function(
            function_name="show_product_details",
            parameters={"product_id": "prod_123"},
            session_id="test"
        )
        
        assert "product" in result
        assert result["product"]["id"] == "prod_123"
    
    @pytest.mark.asyncio
    async def test_mock_agent_execute_cart_function(self):
        """Test mock agent executes add to cart function."""
        agent = MockAIAgent()
        
        result = await agent.execute_function(
            function_name="add_to_cart",
            parameters={"product_id": "prod_123", "quantity": 2},
            session_id="test"
        )
        
        assert "cart_item" in result
        assert "cart_summary" in result
        assert result["cart_item"]["quantity"] == 2
    
    @pytest.mark.asyncio
    async def test_mock_agent_execute_recommendations_function(self):
        """Test mock agent executes recommendations function."""
        agent = MockAIAgent()
        
        result = await agent.execute_function(
            function_name="get_recommendations",
            parameters={"based_on": "prod_123", "max_results": 5},
            session_id="test"
        )
        
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_mock_agent_unknown_function(self):
        """Test mock agent handles unknown function."""
        agent = MockAIAgent()
        
        result = await agent.execute_function(
            function_name="unknown_function",
            parameters={},
            session_id="test"
        )
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_mock_agent_streaming_delay(self):
        """Test mock agent has realistic streaming delays."""
        import time
        agent = MockAIAgent()
        
        start_time = time.time()
        async for chunk in agent.stream_response(
            message="test",
            context={},
            session_id="test"
        ):
            pass
        end_time = time.time()
        
        # Should take some time due to delays
        assert end_time - start_time > 0.1


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


class TestAIAgentFactory:
    """Tests for AI agent factory function."""
    
    def test_create_mock_agent_when_no_provider(self):
        """Test factory creates mock agent when no provider configured."""
        import os
        
        # Clear AI provider settings
        old_provider = os.environ.get("AI_PROVIDER")
        old_openai = os.environ.get("OPENAI_API_KEY")
        old_anthropic = os.environ.get("ANTHROPIC_API_KEY")
        
        if "AI_PROVIDER" in os.environ:
            del os.environ["AI_PROVIDER"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        
        agent = create_ai_agent()
        assert isinstance(agent, MockAIAgent)
        
        # Restore
        if old_provider:
            os.environ["AI_PROVIDER"] = old_provider
        if old_openai:
            os.environ["OPENAI_API_KEY"] = old_openai
        if old_anthropic:
            os.environ["ANTHROPIC_API_KEY"] = old_anthropic
    
    def test_create_openai_agent_when_configured(self):
        """Test factory creates OpenAI agent when configured."""
        import os
        
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test_key"
        
        agent = create_ai_agent()
        assert isinstance(agent, OpenAIAgent)
    
    def test_create_anthropic_agent_when_configured(self):
        """Test factory creates Anthropic agent when configured."""
        import os
        
        os.environ["AI_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        
        agent = create_ai_agent()
        assert isinstance(agent, AnthropicAgent)


class TestAgentErrorHandling:
    """Tests for AI agent error handling."""
    
    @pytest.mark.asyncio
    async def test_mock_agent_handles_empty_message(self):
        """Test mock agent handles empty message."""
        agent = MockAIAgent()
        
        chunks = []
        async for chunk in agent.stream_response(
            message="",
            context={},
            session_id="test"
        ):
            chunks.append(chunk)
        
        # Should still return some response
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_mock_agent_handles_empty_context(self):
        """Test mock agent handles empty context."""
        agent = MockAIAgent()
        
        chunks = []
        async for chunk in agent.stream_response(
            message="test",
            context={},
            session_id="test"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_mock_agent_function_with_missing_params(self):
        """Test mock agent handles missing parameters."""
        agent = MockAIAgent()
        
        result = await agent.execute_function(
            function_name="search_products",
            parameters={},  # Missing required params
            session_id="test"
        )
        
        # Should handle gracefully
        assert isinstance(result, dict)


class TestAgentPerformance:
    """Tests for AI agent performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_mock_agent_streaming_is_async(self):
        """Test mock agent streaming is truly async."""
        agent = MockAIAgent()
        
        # Start streaming
        stream = agent.stream_response(
            message="test",
            context={},
            session_id="test"
        )
        
        # Should be async generator
        assert hasattr(stream, '__anext__')
    
    @pytest.mark.asyncio
    async def test_mock_agent_concurrent_requests(self):
        """Test mock agent can handle concurrent requests."""
        agent = MockAIAgent()
        
        # Create multiple concurrent streams
        async def get_response():
            chunks = []
            async for chunk in agent.stream_response(
                message="test",
                context={},
                session_id="test"
            ):
                chunks.append(chunk)
            return chunks
        
        results = await asyncio.gather(
            get_response(),
            get_response(),
            get_response()
        )
        
        # All should complete successfully
        assert len(results) == 3
        assert all(len(r) > 0 for r in results)

