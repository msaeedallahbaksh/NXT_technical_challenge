"""
Tests for ContextManager - context validation and AI hallucination prevention.

This module tests the context tracking and validation system that prevents
AI hallucination by ensuring function calls only reference recently seen products.
"""

import pytest
from datetime import datetime, timedelta

from context_manager import ContextManager
from models import SearchContext, SessionContext


class TestContextValidation:
    """Tests for product ID validation against search context."""
    
    @pytest.mark.asyncio
    async def test_validate_product_in_recent_search(
        self,
        async_session,
        test_session_id,
        test_search_context
    ):
        """Test validating a product ID that's in recent search results."""
        context_mgr = ContextManager()
        
        result = await context_mgr.validate_product_id(
            test_session_id,
            "test_prod_001",
            async_session
        )
        
        assert result["valid"] is True
        assert "found_in_search" in result
        assert result["found_in_search"] == "headphones"
    
    @pytest.mark.asyncio
    async def test_validate_product_not_in_search(
        self,
        async_session,
        test_session_id,
        test_search_context
    ):
        """Test validating a product ID not in search results."""
        context_mgr = ContextManager()
        
        result = await context_mgr.validate_product_id(
            test_session_id,
            "nonexistent_product",
            async_session
        )
        
        assert result["valid"] is False
        assert "error" in result
        assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_validation_with_no_search_history(
        self,
        async_session,
        test_session_id
    ):
        """Test validation when there's no search history."""
        context_mgr = ContextManager()
        
        result = await context_mgr.validate_product_id(
            test_session_id,
            "test_prod_001",
            async_session
        )
        
        assert result["valid"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_validation_provides_suggestions(
        self,
        async_session,
        test_session_id,
        test_search_context
    ):
        """Test that validation provides similar product suggestions."""
        context_mgr = ContextManager()
        
        # Try a similar but invalid product ID
        result = await context_mgr.validate_product_id(
            test_session_id,
            "test_prod_999",  # Similar format but invalid
            async_session
        )
        
        assert result["valid"] is False
        assert "suggestions" in result
        # May have suggestions if similar product IDs exist
    
    @pytest.mark.asyncio
    async def test_context_window_expiration(
        self,
        async_session,
        test_session_id
    ):
        """Test that old search context expires."""
        context_mgr = ContextManager()
        
        # Create an old search context (more than 30 minutes ago)
        old_time = datetime.utcnow() - timedelta(minutes=35)
        old_search = SearchContext(
            session_id=test_session_id,
            search_query="old search",
            results=["old_product"],
            timestamp=old_time
        )
        async_session.add(old_search)
        await async_session.commit()
        
        # Try to validate old product
        result = await context_mgr.validate_product_id(
            test_session_id,
            "old_product",
            async_session
        )
        
        # Should be invalid because context expired
        assert result["valid"] is False


class TestSearchContextTracking:
    """Tests for tracking search results."""
    
    @pytest.mark.asyncio
    async def test_track_search_results(
        self,
        async_session,
        test_session_id
    ):
        """Test tracking new search results."""
        context_mgr = ContextManager()
        
        await context_mgr.track_search_results(
            test_session_id,
            "laptops",
            ["prod_1", "prod_2", "prod_3"],
            category="electronics",
            session_db=async_session
        )
        
        # Verify search was tracked
        from sqlmodel import select
        statement = select(SearchContext).where(
            SearchContext.session_id == test_session_id,
            SearchContext.search_query == "laptops"
        )
        result = await async_session.execute(statement)
        search = result.scalar_one_or_none()
        
        assert search is not None
        assert search.results == ["prod_1", "prod_2", "prod_3"]
        assert search.category == "electronics"
    
    @pytest.mark.asyncio
    async def test_track_multiple_searches(
        self,
        async_session,
        test_session_id
    ):
        """Test tracking multiple searches."""
        context_mgr = ContextManager()
        
        # Track first search
        await context_mgr.track_search_results(
            test_session_id,
            "headphones",
            ["prod_1", "prod_2"],
            session_db=async_session
        )
        
        # Track second search
        await context_mgr.track_search_results(
            test_session_id,
            "laptops",
            ["prod_3", "prod_4"],
            session_db=async_session
        )
        
        # Both searches should be tracked
        from sqlmodel import select
        statement = select(SearchContext).where(
            SearchContext.session_id == test_session_id
        )
        result = await async_session.execute(statement)
        searches = result.scalars().all()
        
        assert len(searches) == 2


class TestSessionContext:
    """Tests for session context management."""
    
    @pytest.mark.asyncio
    async def test_check_session_exists(
        self,
        async_session,
        test_session_context
    ):
        """Test checking if session exists."""
        context_mgr = ContextManager()
        
        exists = await context_mgr.session_exists(
            test_session_context.session_id,
            async_session
        )
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_check_nonexistent_session(
        self,
        async_session
    ):
        """Test checking for non-existent session."""
        context_mgr = ContextManager()
        
        exists = await context_mgr.session_exists(
            "nonexistent_session",
            async_session
        )
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_get_session_context(
        self,
        async_session,
        test_session_context
    ):
        """Test retrieving session context."""
        context_mgr = ContextManager()
        
        context = await context_mgr.get_context(
            test_session_context.session_id,
            async_session
        )
        
        assert context is not None
        assert context.session_id == test_session_context.session_id
        assert "cart_items" in context.context_data
    
    @pytest.mark.asyncio
    async def test_update_existing_context(
        self,
        async_session,
        test_session_context
    ):
        """Test updating existing session context."""
        context_mgr = ContextManager()
        
        new_data = {
            "recent_searches": ["laptops", "headphones"],
            "viewed_products": ["prod_1", "prod_2"]
        }
        
        await context_mgr.update_context(
            test_session_context.session_id,
            new_data,
            async_session
        )
        
        # Verify update
        updated = await context_mgr.get_context(
            test_session_context.session_id,
            async_session
        )
        
        assert updated.context_data["recent_searches"] == ["laptops", "headphones"]
        assert updated.context_data["viewed_products"] == ["prod_1", "prod_2"]
    
    @pytest.mark.asyncio
    async def test_create_new_context(
        self,
        async_session,
        test_session_id
    ):
        """Test creating new session context."""
        context_mgr = ContextManager()
        
        context_data = {
            "cart_items": [],
            "recent_searches": ["test"]
        }
        
        await context_mgr.update_context(
            test_session_id,
            context_data,
            async_session
        )
        
        # Verify creation
        context = await context_mgr.get_context(
            test_session_id,
            async_session
        )
        
        assert context is not None
        assert context.session_id == test_session_id


class TestRecentProducts:
    """Tests for retrieving recent products."""
    
    @pytest.mark.asyncio
    async def test_get_recent_products(
        self,
        async_session,
        test_session_id
    ):
        """Test getting recently searched products."""
        context_mgr = ContextManager()
        
        # Track some searches
        await context_mgr.track_search_results(
            test_session_id,
            "query1",
            ["prod_1", "prod_2"],
            session_db=async_session
        )
        await context_mgr.track_search_results(
            test_session_id,
            "query2",
            ["prod_3", "prod_4"],
            session_db=async_session
        )
        
        # Get recent products
        recent = await context_mgr.get_recent_products(
            test_session_id,
            limit=10,
            session=async_session
        )
        
        assert len(recent) > 0
        assert "prod_1" in recent or "prod_2" in recent or "prod_3" in recent
    
    @pytest.mark.asyncio
    async def test_recent_products_limit(
        self,
        async_session,
        test_session_id
    ):
        """Test recent products respects limit."""
        context_mgr = ContextManager()
        
        # Track search with many products
        products = [f"prod_{i}" for i in range(20)]
        await context_mgr.track_search_results(
            test_session_id,
            "query",
            products,
            session_db=async_session
        )
        
        # Get with limit
        recent = await context_mgr.get_recent_products(
            test_session_id,
            limit=5,
            session=async_session
        )
        
        assert len(recent) <= 5
    
    @pytest.mark.asyncio
    async def test_recent_products_unique(
        self,
        async_session,
        test_session_id
    ):
        """Test recent products doesn't return duplicates."""
        context_mgr = ContextManager()
        
        # Track searches with overlapping products
        await context_mgr.track_search_results(
            test_session_id,
            "query1",
            ["prod_1", "prod_2"],
            session_db=async_session
        )
        await context_mgr.track_search_results(
            test_session_id,
            "query2",
            ["prod_1", "prod_3"],  # prod_1 repeated
            session_db=async_session
        )
        
        recent = await context_mgr.get_recent_products(
            test_session_id,
            session=async_session
        )
        
        # Check for uniqueness
        assert len(recent) == len(set(recent))


class TestSimilarityCalculation:
    """Tests for product ID similarity calculation."""
    
    def test_exact_match_similarity(self):
        """Test similarity calculation for exact matches."""
        context_mgr = ContextManager()
        
        similarity = context_mgr._calculate_similarity(
            "prod_001",
            "prod_001"
        )
        
        assert similarity == 1.0
    
    def test_similar_strings_similarity(self):
        """Test similarity for similar strings."""
        context_mgr = ContextManager()
        
        similarity = context_mgr._calculate_similarity(
            "prod_001",
            "prod_002"
        )
        
        # Should have some similarity
        assert 0 < similarity < 1.0
    
    def test_different_strings_similarity(self):
        """Test similarity for very different strings."""
        context_mgr = ContextManager()
        
        similarity = context_mgr._calculate_similarity(
            "prod_001",
            "xyz_999"
        )
        
        # Should have low similarity
        assert similarity < 1.0


class TestContextCleanup:
    """Tests for old context cleanup."""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_search_context(
        self,
        async_session,
        test_session_id
    ):
        """Test that old search context is cleaned up."""
        context_mgr = ContextManager()
        
        # Create old search context
        old_time = datetime.utcnow() - timedelta(hours=3)
        old_search = SearchContext(
            session_id=test_session_id,
            search_query="old",
            results=["prod_1"],
            timestamp=old_time
        )
        async_session.add(old_search)
        await async_session.commit()
        
        # Track new search (this triggers cleanup)
        await context_mgr.track_search_results(
            test_session_id,
            "new search",
            ["prod_2"],
            session_db=async_session
        )
        
        # Verify old context was cleaned
        from sqlmodel import select
        statement = select(SearchContext).where(
            SearchContext.session_id == test_session_id
        )
        result = await async_session.execute(statement)
        searches = result.scalars().all()
        
        # Should only have new search
        search_queries = [s.search_query for s in searches]
        assert "new search" in search_queries
        # Old search should be gone
        assert "old" not in search_queries or len(searches) == 1

