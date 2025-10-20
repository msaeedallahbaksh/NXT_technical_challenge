"""
Tests for API endpoints including function calls, sessions, and utility endpoints.

This module tests all REST API endpoints for proper functionality,
error handling, and response validation.
"""

import pytest
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient

from models import Product, ProductCategory


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, test_client: TestClient):
        """Test health check returns 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "rate_limiting" in data
    
    def test_health_check_contains_rate_limiting_info(self, test_client: TestClient):
        """Test health check includes rate limiting configuration."""
        response = test_client.get("/health")
        data = response.json()
        
        assert "rate_limiting" in data
        assert "enabled" in data["rate_limiting"]
        assert "limit" in data["rate_limiting"]


class TestSessionEndpoints:
    """Tests for session management endpoints."""
    
    def test_create_session(self, test_client: TestClient):
        """Test session creation."""
        response = test_client.post("/api/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert "created_at" in data
        assert len(data["session_id"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_session_context(
        self,
        async_test_client: AsyncClient,
        test_session_context
    ):
        """Test retrieving session context."""
        response = await async_test_client.get(
            f"/api/sessions/{test_session_context.session_id}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == test_session_context.session_id
        assert "context_data" in data
        assert "created_at" in data
    
    def test_get_nonexistent_session(self, test_client: TestClient):
        """Test getting a session that doesn't exist."""
        response = test_client.get("/api/sessions/nonexistent_session_id")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data or "detail" in data


class TestSearchProductsEndpoint:
    """Tests for product search endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_products_success(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products
    ):
        """Test successful product search."""
        request_body = {
            "query": "headphones",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/search_products",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "products" in data["data"]
        assert "total_results" in data["data"]
        assert "context_updated" in data["data"]
    
    @pytest.mark.asyncio
    async def test_search_with_category_filter(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products
    ):
        """Test product search with category filter."""
        request_body = {
            "query": "test",
            "category": "electronics",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/search_products",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        products = data["data"]["products"]
        
        # All products should be in electronics category
        for product in products:
            assert product["category"] == "electronics"
    
    @pytest.mark.asyncio
    async def test_search_with_limit(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products
    ):
        """Test product search with result limit."""
        request_body = {
            "query": "test",
            "limit": 2,
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/search_products",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        products = data["data"]["products"]
        assert len(products) <= 2
    
    @pytest.mark.asyncio
    async def test_search_no_results(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products
    ):
        """Test product search with no matching results."""
        request_body = {
            "query": "nonexistent_product_xyz",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/search_products",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["total_results"] == 0
        assert len(data["data"]["products"]) == 0
    
    def test_search_missing_session_id(
        self,
        test_client: TestClient
    ):
        """Test search without session_id."""
        request_body = {
            "query": "headphones"
        }
        
        response = test_client.post(
            "/api/functions/search_products",
            json=request_body
        )
        assert response.status_code == 422  # Validation error


class TestProductDetailsEndpoint:
    """Tests for product details endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_product_details_success(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context,
        sample_products
    ):
        """Test getting product details successfully."""
        request_body = {
            "product_id": "test_prod_001",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/show_product_details",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "product" in data["data"]
        assert data["data"]["product"]["id"] == "test_prod_001"
        assert "validation" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_product_details_with_recommendations(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context,
        sample_products
    ):
        """Test getting product details with recommendations."""
        request_body = {
            "product_id": "test_prod_001",
            "include_recommendations": True,
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/show_product_details",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        # Recommendations may or may not be present depending on available products
        assert "product" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_product_details_invalid_id(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context
    ):
        """Test getting details for non-existent product."""
        request_body = {
            "product_id": "invalid_product_id",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/show_product_details",
            json=request_body
        )
        
        # Should return error due to validation failure
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    @pytest.mark.asyncio
    async def test_context_validation_prevents_hallucination(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context
    ):
        """Test that context validation prevents AI hallucination."""
        # Try to access a product that wasn't in search results
        request_body = {
            "product_id": "test_prod_003",  # Not in search context
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/show_product_details",
            json=request_body
        )
        
        data = response.json()
        # Should fail validation since product wasn't in search results
        assert data["success"] is False
        assert "validation" in data or "error" in data


class TestAddToCartEndpoint:
    """Tests for add to cart endpoint."""
    
    @pytest.mark.asyncio
    async def test_add_to_cart_success(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context,
        sample_products
    ):
        """Test successfully adding item to cart."""
        request_body = {
            "product_id": "test_prod_001",
            "quantity": 2,
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/add_to_cart",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "cart_item" in data["data"]
        assert "cart_summary" in data["data"]
        assert data["data"]["cart_item"]["quantity"] == 2
    
    @pytest.mark.asyncio
    async def test_add_to_cart_default_quantity(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context,
        sample_products
    ):
        """Test adding to cart with default quantity of 1."""
        request_body = {
            "product_id": "test_prod_001",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/add_to_cart",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["cart_item"]["quantity"] == 1
    
    @pytest.mark.asyncio
    async def test_add_to_cart_invalid_product(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_search_context
    ):
        """Test adding non-existent product to cart."""
        request_body = {
            "product_id": "invalid_product",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/add_to_cart",
            json=request_body
        )
        
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    @pytest.mark.asyncio
    async def test_add_to_cart_out_of_stock(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products,
        async_session
    ):
        """Test adding out of stock product to cart."""
        # First add the out of stock product to search context
        from context_manager import ContextManager
        context_mgr = ContextManager()
        await context_mgr.track_search_results(
            test_session_id,
            "test",
            ["test_prod_004"],
            session_db=async_session
        )
        
        request_body = {
            "product_id": "test_prod_004",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/add_to_cart",
            json=request_body
        )
        
        data = response.json()
        assert data["success"] is False
        assert "out of stock" in data["error"].lower() or "not available" in data["error"].lower()
    
    def test_add_to_cart_invalid_quantity(
        self,
        test_client: TestClient,
        test_session_id: str
    ):
        """Test adding item with invalid quantity."""
        request_body = {
            "product_id": "test_prod_001",
            "quantity": 0,  # Invalid quantity
            "session_id": test_session_id
        }
        
        response = test_client.post(
            "/api/functions/add_to_cart",
            json=request_body
        )
        
        assert response.status_code == 422  # Validation error


class TestRemoveFromCartEndpoint:
    """Tests for remove from cart endpoint."""
    
    @pytest.mark.asyncio
    async def test_remove_from_cart_success(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_cart_item
    ):
        """Test successfully removing item from cart."""
        request_body = {
            "product_id": test_cart_item.product_id,
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/remove_from_cart",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "message" in data["data"]
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_cart_item(
        self,
        async_test_client: AsyncClient,
        test_session_id: str
    ):
        """Test removing item that's not in cart."""
        request_body = {
            "product_id": "nonexistent_product",
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/remove_from_cart",
            json=request_body
        )
        
        # Should handle gracefully
        data = response.json()
        # Either succeeds with message or returns error
        assert "success" in data or "error" in data


class TestGetRecommendationsEndpoint:
    """Tests for product recommendations endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_recommendations_by_product(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products
    ):
        """Test getting recommendations based on product."""
        request_body = {
            "based_on": "test_prod_001",
            "max_results": 5,
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/get_recommendations",
            json=request_body
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "recommendations" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_recommendations_limit(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        sample_products
    ):
        """Test recommendations with result limit."""
        request_body = {
            "based_on": "test_prod_001",
            "max_results": 2,
            "session_id": test_session_id
        }
        
        response = await async_test_client.post(
            "/api/functions/get_recommendations",
            json=request_body
        )
        
        data = response.json()
        recommendations = data["data"]["recommendations"]
        assert len(recommendations) <= 2


class TestGetCartEndpoint:
    """Tests for get cart endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_empty_cart(
        self,
        async_test_client: AsyncClient,
        test_session_id: str
    ):
        """Test getting an empty cart."""
        response = await async_test_client.get(
            f"/api/cart/{test_session_id}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        assert data["summary"]["total_items"] == 0
    
    @pytest.mark.asyncio
    async def test_get_cart_with_items(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_cart_item
    ):
        """Test getting cart with items."""
        response = await async_test_client.get(
            f"/api/cart/{test_session_id}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) > 0
        assert data["summary"]["total_items"] > 0
        assert "subtotal" in data["summary"]


class TestClearCartEndpoint:
    """Tests for clear cart endpoint."""
    
    @pytest.mark.asyncio
    async def test_clear_cart(
        self,
        async_test_client: AsyncClient,
        test_session_id: str,
        test_cart_item
    ):
        """Test clearing cart."""
        response = await async_test_client.delete(
            f"/api/cart/{test_session_id}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"]
        
        # Verify cart is empty
        get_response = await async_test_client.get(
            f"/api/cart/{test_session_id}"
        )
        cart_data = get_response.json()
        assert cart_data["summary"]["total_items"] == 0

