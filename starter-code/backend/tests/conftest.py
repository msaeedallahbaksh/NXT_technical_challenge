"""
Test configuration and shared fixtures for pytest.

This module provides test fixtures for database setup, test clients,
and mock data for comprehensive backend testing.
"""

# CRITICAL: Set test environment variables BEFORE any other imports
# This ensures that when we import main.py, it uses test configuration
import os
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["RATE_LIMITING_ENABLED"] = "false"
os.environ["SKIP_DB_INIT"] = "true"

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path

# Add parent directory to path so we can import from parent
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from main import app
from database import get_session
from models import (
    Product, ProductCategory, SessionContext, SearchContext, 
    CartItem, ConversationMessage
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create async test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session."""
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def test_client(async_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create test client with database session override."""
    
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_test_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for testing async operations."""
    
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def sample_products(async_session: AsyncSession):
    """Create sample products in test database."""
    products = [
        Product(
            id="test_prod_001",
            name="Test Headphones",
            description="High-quality test headphones",
            price=199.99,
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/image1.jpg",
            in_stock=True,
            stock_quantity=10,
            rating=4.5,
            reviews_count=100,
            features=["Noise Cancellation", "Wireless"],
            specifications={"brand": "TestBrand", "model": "TB-100"}
        ),
        Product(
            id="test_prod_002",
            name="Test Laptop",
            description="Powerful test laptop",
            price=999.99,
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/image2.jpg",
            in_stock=True,
            stock_quantity=5,
            rating=4.8,
            reviews_count=250,
            features=["16GB RAM", "512GB SSD"],
            specifications={"brand": "TestBrand", "model": "TB-200"}
        ),
        Product(
            id="test_prod_003",
            name="Test T-Shirt",
            description="Comfortable test t-shirt",
            price=24.99,
            category=ProductCategory.CLOTHING,
            image_url="https://test.com/image3.jpg",
            in_stock=True,
            stock_quantity=50,
            rating=4.0,
            reviews_count=75,
            features=["100% Cotton", "Machine Washable"],
            specifications={"material": "Cotton", "care": "Machine Wash"}
        ),
        Product(
            id="test_prod_004",
            name="Out of Stock Product",
            description="This product is out of stock",
            price=49.99,
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/image4.jpg",
            in_stock=False,
            stock_quantity=0,
            rating=4.2,
            reviews_count=30,
            features=["Feature 1"],
            specifications={"spec": "value"}
        )
    ]
    
    for product in products:
        async_session.add(product)
    await async_session.commit()
    
    # Refresh to get current state
    for product in products:
        await async_session.refresh(product)
    
    return products


@pytest.fixture(scope="function")
def test_session_id() -> str:
    """Generate a test session ID."""
    return "test_session_123"


@pytest_asyncio.fixture(scope="function")
async def test_session_context(
    async_session: AsyncSession,
    test_session_id: str
):
    """Create a test session context."""
    context = SessionContext(
        session_id=test_session_id,
        context_data={
            "cart_items": [],
            "recent_searches": [],
            "viewed_products": []
        }
    )
    async_session.add(context)
    await async_session.commit()
    await async_session.refresh(context)
    return context


@pytest_asyncio.fixture(scope="function")
async def test_search_context(
    async_session: AsyncSession,
    test_session_id: str,
    sample_products
):
    """Create a test search context."""
    search_ctx = SearchContext(
        session_id=test_session_id,
        search_query="headphones",
        results=["test_prod_001", "test_prod_002"],
        category=ProductCategory.ELECTRONICS
    )
    async_session.add(search_ctx)
    await async_session.commit()
    await async_session.refresh(search_ctx)
    return search_ctx


@pytest_asyncio.fixture(scope="function")
async def test_cart_item(
    async_session: AsyncSession,
    test_session_id: str,
    sample_products
):
    """Create a test cart item."""
    product = sample_products[0]
    cart_item = CartItem(
        session_id=test_session_id,
        product_id=product.id,
        quantity=2,
        unit_price=product.price,
        total_price=product.price * 2
    )
    async_session.add(cart_item)
    await async_session.commit()
    await async_session.refresh(cart_item)
    return cart_item


@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing."""
    return {
        "type": "text",
        "content": "Here are some great products for you!"
    }


@pytest.fixture
def mock_function_call():
    """Mock function call for testing."""
    return {
        "name": "search_products",
        "parameters": {
            "query": "headphones",
            "category": "electronics",
            "limit": 10
        }
    }
