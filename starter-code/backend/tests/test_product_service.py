"""
Tests for ProductService - product search, details, and recommendations.

This module tests the product service layer that handles all product-related
operations including search, retrieval, and recommendations.
"""

import pytest

from product_service import ProductService
from models import Product, ProductCategory


class TestProductSearch:
    """Tests for product search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_products_by_name(
        self,
        async_session,
        sample_products
    ):
        """Test searching products by name."""
        service = ProductService()
        
        results = await service.search_products(
            query="headphones",
            session=async_session
        )
        
        assert len(results) > 0
        assert any("headphones" in p.name.lower() for p in results)
    
    @pytest.mark.asyncio
    async def test_search_products_by_description(
        self,
        async_session,
        sample_products
    ):
        """Test searching products by description."""
        service = ProductService()
        
        results = await service.search_products(
            query="laptop",
            session=async_session
        )
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_search_with_category_filter(
        self,
        async_session,
        sample_products
    ):
        """Test searching with category filter."""
        service = ProductService()
        
        results = await service.search_products(
            query="test",
            category=ProductCategory.ELECTRONICS,
            session=async_session
        )
        
        # All results should be electronics
        for product in results:
            assert product.category == ProductCategory.ELECTRONICS
    
    @pytest.mark.asyncio
    async def test_search_with_limit(
        self,
        async_session,
        sample_products
    ):
        """Test search respects result limit."""
        service = ProductService()
        
        results = await service.search_products(
            query="test",
            limit=2,
            session=async_session
        )
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_only_in_stock(
        self,
        async_session,
        sample_products
    ):
        """Test search only returns in-stock products."""
        service = ProductService()
        
        results = await service.search_products(
            query="test",
            session=async_session
        )
        
        # All results should be in stock
        for product in results:
            assert product.in_stock is True
    
    @pytest.mark.asyncio
    async def test_search_no_results(
        self,
        async_session,
        sample_products
    ):
        """Test search with no matching products."""
        service = ProductService()
        
        results = await service.search_products(
            query="nonexistent_product_xyz123",
            session=async_session
        )
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_case_insensitive(
        self,
        async_session,
        sample_products
    ):
        """Test search is case insensitive."""
        service = ProductService()
        
        results_lower = await service.search_products(
            query="headphones",
            session=async_session
        )
        
        results_upper = await service.search_products(
            query="HEADPHONES",
            session=async_session
        )
        
        # Should return same results
        assert len(results_lower) == len(results_upper)


class TestGetProductByID:
    """Tests for getting product by ID."""
    
    @pytest.mark.asyncio
    async def test_get_existing_product(
        self,
        async_session,
        sample_products
    ):
        """Test getting an existing product by ID."""
        service = ProductService()
        
        product = await service.get_product_by_id(
            "test_prod_001",
            session=async_session
        )
        
        assert product is not None
        assert product.id == "test_prod_001"
        assert product.name == "Test Headphones"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_product(
        self,
        async_session,
        sample_products
    ):
        """Test getting a non-existent product."""
        service = ProductService()
        
        product = await service.get_product_by_id(
            "nonexistent_id",
            session=async_session
        )
        
        assert product is None
    
    @pytest.mark.asyncio
    async def test_get_product_includes_all_fields(
        self,
        async_session,
        sample_products
    ):
        """Test that getting product includes all expected fields."""
        service = ProductService()
        
        product = await service.get_product_by_id(
            "test_prod_001",
            session=async_session
        )
        
        assert product is not None
        assert hasattr(product, 'id')
        assert hasattr(product, 'name')
        assert hasattr(product, 'description')
        assert hasattr(product, 'price')
        assert hasattr(product, 'category')
        assert hasattr(product, 'in_stock')
        assert hasattr(product, 'features')
        assert hasattr(product, 'specifications')


class TestGetRecommendations:
    """Tests for product recommendations."""
    
    @pytest.mark.asyncio
    async def test_get_recommendations_same_category(
        self,
        async_session,
        sample_products
    ):
        """Test recommendations are from same category."""
        service = ProductService()
        
        recommendations = await service.get_recommendations(
            based_on_product_id="test_prod_001",
            session=async_session
        )
        
        # Get base product
        base_product = await service.get_product_by_id(
            "test_prod_001",
            session=async_session
        )
        
        # All recommendations should be same category
        for rec in recommendations:
            assert rec.category == base_product.category
    
    @pytest.mark.asyncio
    async def test_get_recommendations_excludes_base_product(
        self,
        async_session,
        sample_products
    ):
        """Test recommendations don't include the base product."""
        service = ProductService()
        
        recommendations = await service.get_recommendations(
            based_on_product_id="test_prod_001",
            session=async_session
        )
        
        # Base product should not be in recommendations
        rec_ids = [r.id for r in recommendations]
        assert "test_prod_001" not in rec_ids
    
    @pytest.mark.asyncio
    async def test_get_recommendations_with_limit(
        self,
        async_session,
        sample_products
    ):
        """Test recommendations respect limit."""
        service = ProductService()
        
        recommendations = await service.get_recommendations(
            based_on_product_id="test_prod_001",
            limit=2,
            session=async_session
        )
        
        assert len(recommendations) <= 2
    
    @pytest.mark.asyncio
    async def test_get_recommendations_invalid_product(
        self,
        async_session,
        sample_products
    ):
        """Test recommendations for non-existent product."""
        service = ProductService()
        
        recommendations = await service.get_recommendations(
            based_on_product_id="nonexistent_product",
            session=async_session
        )
        
        # Should return empty list
        assert len(recommendations) == 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations_only_in_stock(
        self,
        async_session,
        sample_products
    ):
        """Test recommendations only include in-stock products."""
        service = ProductService()
        
        recommendations = await service.get_recommendations(
            based_on_product_id="test_prod_001",
            session=async_session
        )
        
        # All recommendations should be in stock
        for rec in recommendations:
            assert rec.in_stock is True


class TestMockImplementations:
    """Tests for mock implementations (when no session provided)."""
    
    @pytest.mark.asyncio
    async def test_mock_search_products(self):
        """Test mock product search works without session."""
        service = ProductService()
        
        results = await service.search_products(
            query="headphones",
            session=None  # No session, should use mock
        )
        
        # Should return some results from mock data
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_mock_get_product(self):
        """Test mock get product works without session."""
        service = ProductService()
        
        product = await service.get_product_by_id(
            "prod_001",
            session=None
        )
        
        # Mock implementation might return product
        assert product is None or isinstance(product, Product)
    
    @pytest.mark.asyncio
    async def test_mock_recommendations(self):
        """Test mock recommendations work without session."""
        service = ProductService()
        
        recommendations = await service.get_recommendations(
            based_on_product_id="prod_001",
            session=None
        )
        
        assert isinstance(recommendations, list)


class TestProductDataIntegrity:
    """Tests for product data validation and integrity."""
    
    @pytest.mark.asyncio
    async def test_product_price_non_negative(
        self,
        async_session,
        sample_products
    ):
        """Test all products have non-negative prices."""
        service = ProductService()
        
        results = await service.search_products(
            query="",
            session=async_session
        )
        
        for product in results:
            assert product.price >= 0
    
    @pytest.mark.asyncio
    async def test_product_stock_quantity_valid(
        self,
        async_session,
        sample_products
    ):
        """Test stock quantities are valid."""
        service = ProductService()
        
        results = await service.search_products(
            query="",
            session=async_session
        )
        
        for product in results:
            assert product.stock_quantity >= 0
            # If in_stock is True, should have quantity > 0
            if product.in_stock:
                assert product.stock_quantity > 0
    
    @pytest.mark.asyncio
    async def test_product_rating_valid_range(
        self,
        async_session,
        sample_products
    ):
        """Test product ratings are in valid range."""
        service = ProductService()
        
        results = await service.search_products(
            query="",
            session=async_session
        )
        
        for product in results:
            if product.rating is not None:
                assert 0 <= product.rating <= 5
    
    @pytest.mark.asyncio
    async def test_product_has_required_fields(
        self,
        async_session,
        sample_products
    ):
        """Test products have all required fields."""
        service = ProductService()
        
        product = await service.get_product_by_id(
            "test_prod_001",
            session=async_session
        )
        
        # Required fields
        assert product.id
        assert product.name
        assert product.description
        assert product.price is not None
        assert product.category
        assert product.image_url
        assert product.in_stock is not None

