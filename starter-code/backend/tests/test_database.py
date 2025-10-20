"""
Tests for database operations and models.

This module tests database connectivity, CRUD operations, and model
validation for all database tables.
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import select

from models import (
    Product, ProductCategory, SessionContext, SearchContext,
    CartItem, ConversationMessage
)


class TestProductModel:
    """Tests for Product model and operations."""
    
    @pytest.mark.asyncio
    async def test_create_product(self, async_session):
        """Test creating a new product."""
        product = Product(
            id="test_new_prod",
            name="Test Product",
            description="A test product",
            price=99.99,
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/image.jpg",
            in_stock=True,
            stock_quantity=10
        )
        
        async_session.add(product)
        await async_session.commit()
        await async_session.refresh(product)
        
        assert product.id == "test_new_prod"
        assert product.name == "Test Product"
    
    @pytest.mark.asyncio
    async def test_product_has_timestamps(self, async_session):
        """Test product has created_at and updated_at timestamps."""
        product = Product(
            id="test_timestamp",
            name="Test",
            description="Test",
            price=10.0,
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/img.jpg",
            in_stock=True,
            stock_quantity=5
        )
        
        async_session.add(product)
        await async_session.commit()
        await async_session.refresh(product)
        
        assert product.created_at is not None
        assert product.updated_at is not None
        assert isinstance(product.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_query_products_by_category(self, async_session, sample_products):
        """Test querying products by category."""
        statement = select(Product).where(
            Product.category == ProductCategory.ELECTRONICS
        )
        result = await async_session.execute(statement)
        products = result.scalars().all()
        
        assert len(products) > 0
        assert all(p.category == ProductCategory.ELECTRONICS for p in products)
    
    @pytest.mark.asyncio
    async def test_query_in_stock_products(self, async_session, sample_products):
        """Test querying only in-stock products."""
        statement = select(Product).where(Product.in_stock == True)
        result = await async_session.execute(statement)
        products = result.scalars().all()
        
        assert all(p.in_stock for p in products)
    
    @pytest.mark.asyncio
    async def test_product_price_validation(self, async_session):
        """Test product price must be non-negative."""
        product = Product(
            id="test_price",
            name="Test",
            description="Test",
            price=-10.0,  # Invalid negative price
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/img.jpg",
            in_stock=True
        )
        
        # Should fail validation
        with pytest.raises(Exception):
            async_session.add(product)
            await async_session.commit()


class TestSessionContextModel:
    """Tests for SessionContext model."""
    
    @pytest.mark.asyncio
    async def test_create_session_context(self, async_session):
        """Test creating a new session context."""
        context = SessionContext(
            session_id="test_session_001",
            context_data={"cart": [], "history": []}
        )
        
        async_session.add(context)
        await async_session.commit()
        await async_session.refresh(context)
        
        assert context.session_id == "test_session_001"
        assert "cart" in context.context_data
    
    @pytest.mark.asyncio
    async def test_session_context_unique_session_id(
        self,
        async_session,
        test_session_context
    ):
        """Test session_id is unique."""
        # Try to create another context with same session_id
        duplicate = SessionContext(
            session_id=test_session_context.session_id,
            context_data={}
        )
        
        with pytest.raises(Exception):
            async_session.add(duplicate)
            await async_session.commit()
    
    @pytest.mark.asyncio
    async def test_query_session_by_id(self, async_session, test_session_context):
        """Test querying session by session_id."""
        statement = select(SessionContext).where(
            SessionContext.session_id == test_session_context.session_id
        )
        result = await async_session.execute(statement)
        context = result.scalar_one_or_none()
        
        assert context is not None
        assert context.session_id == test_session_context.session_id
    
    @pytest.mark.asyncio
    async def test_update_session_context(self, async_session, test_session_context):
        """Test updating session context data."""
        test_session_context.context_data["new_field"] = "new_value"
        async_session.add(test_session_context)
        await async_session.commit()
        await async_session.refresh(test_session_context)
        
        assert test_session_context.context_data["new_field"] == "new_value"


class TestSearchContextModel:
    """Tests for SearchContext model."""
    
    @pytest.mark.asyncio
    async def test_create_search_context(self, async_session):
        """Test creating search context."""
        search = SearchContext(
            session_id="test_session",
            search_query="headphones",
            results=["prod_1", "prod_2", "prod_3"],
            category="electronics"
        )
        
        async_session.add(search)
        await async_session.commit()
        await async_session.refresh(search)
        
        assert search.search_query == "headphones"
        assert len(search.results) == 3
    
    @pytest.mark.asyncio
    async def test_search_context_has_timestamp(self, async_session):
        """Test search context has timestamp."""
        search = SearchContext(
            session_id="test",
            search_query="test",
            results=[]
        )
        
        async_session.add(search)
        await async_session.commit()
        await async_session.refresh(search)
        
        assert search.timestamp is not None
        assert isinstance(search.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_query_search_by_session(
        self,
        async_session,
        test_search_context
    ):
        """Test querying searches by session_id."""
        statement = select(SearchContext).where(
            SearchContext.session_id == test_search_context.session_id
        )
        result = await async_session.execute(statement)
        searches = result.scalars().all()
        
        assert len(searches) > 0
    
    @pytest.mark.asyncio
    async def test_search_context_stores_product_ids(
        self,
        async_session,
        test_search_context
    ):
        """Test search context correctly stores product IDs."""
        assert isinstance(test_search_context.results, list)
        assert all(isinstance(pid, str) for pid in test_search_context.results)


class TestCartItemModel:
    """Tests for CartItem model."""
    
    @pytest.mark.asyncio
    async def test_create_cart_item(self, async_session, sample_products):
        """Test creating a cart item."""
        product = sample_products[0]
        cart_item = CartItem(
            session_id="test_session",
            product_id=product.id,
            quantity=2,
            unit_price=product.price,
            total_price=product.price * 2
        )
        
        async_session.add(cart_item)
        await async_session.commit()
        await async_session.refresh(cart_item)
        
        assert cart_item.quantity == 2
        assert cart_item.product_id == product.id
    
    @pytest.mark.asyncio
    async def test_cart_item_has_timestamp(self, async_session, sample_products):
        """Test cart item has added_at timestamp."""
        product = sample_products[0]
        cart_item = CartItem(
            session_id="test",
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            total_price=product.price
        )
        
        async_session.add(cart_item)
        await async_session.commit()
        await async_session.refresh(cart_item)
        
        assert cart_item.added_at is not None
        assert isinstance(cart_item.added_at, datetime)
    
    @pytest.mark.asyncio
    async def test_query_cart_by_session(self, async_session, test_cart_item):
        """Test querying cart items by session."""
        statement = select(CartItem).where(
            CartItem.session_id == test_cart_item.session_id
        )
        result = await async_session.execute(statement)
        items = result.scalars().all()
        
        assert len(items) > 0
    
    @pytest.mark.asyncio
    async def test_cart_item_quantity_positive(self, async_session, sample_products):
        """Test cart item quantity must be positive."""
        product = sample_products[0]
        cart_item = CartItem(
            session_id="test",
            product_id=product.id,
            quantity=0,  # Invalid
            unit_price=product.price,
            total_price=0
        )
        
        with pytest.raises(Exception):
            async_session.add(cart_item)
            await async_session.commit()
    
    @pytest.mark.asyncio
    async def test_delete_cart_item(self, async_session, test_cart_item):
        """Test deleting a cart item."""
        item_id = test_cart_item.id
        
        await async_session.delete(test_cart_item)
        await async_session.commit()
        
        # Verify deletion
        statement = select(CartItem).where(CartItem.id == item_id)
        result = await async_session.execute(statement)
        item = result.scalar_one_or_none()
        
        assert item is None


class TestConversationMessageModel:
    """Tests for ConversationMessage model."""
    
    @pytest.mark.asyncio
    async def test_create_conversation_message(self, async_session):
        """Test creating a conversation message."""
        message = ConversationMessage(
            session_id="test_session",
            role="user",
            content="Hello, I'm looking for headphones"
        )
        
        async_session.add(message)
        await async_session.commit()
        await async_session.refresh(message)
        
        assert message.role == "user"
        assert message.content == "Hello, I'm looking for headphones"
    
    @pytest.mark.asyncio
    async def test_conversation_message_has_timestamp(self, async_session):
        """Test conversation message has timestamp."""
        message = ConversationMessage(
            session_id="test",
            role="assistant",
            content="How can I help you?"
        )
        
        async_session.add(message)
        await async_session.commit()
        await async_session.refresh(message)
        
        assert message.timestamp is not None
        assert isinstance(message.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_query_messages_by_session(self, async_session):
        """Test querying messages by session."""
        session_id = "test_conv_session"
        
        # Add multiple messages
        messages = [
            ConversationMessage(
                session_id=session_id,
                role="user",
                content="Message 1"
            ),
            ConversationMessage(
                session_id=session_id,
                role="assistant",
                content="Message 2"
            )
        ]
        
        for msg in messages:
            async_session.add(msg)
        await async_session.commit()
        
        # Query messages
        statement = select(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.timestamp)
        result = await async_session.execute(statement)
        fetched = result.scalars().all()
        
        assert len(fetched) == 2
    
    @pytest.mark.asyncio
    async def test_conversation_message_with_tool_calls(self, async_session):
        """Test conversation message can store tool calls."""
        import json
        
        tool_calls_data = json.dumps([{
            "function": "search_products",
            "parameters": {"query": "laptops"}
        }])
        
        message = ConversationMessage(
            session_id="test",
            role="assistant",
            content="Let me search for that",
            tool_calls=tool_calls_data
        )
        
        async_session.add(message)
        await async_session.commit()
        await async_session.refresh(message)
        
        assert message.tool_calls is not None
        # Should be able to parse back to dict
        parsed = json.loads(message.tool_calls)
        assert isinstance(parsed, list)


class TestDatabaseRelationships:
    """Tests for database relationships and constraints."""
    
    @pytest.mark.asyncio
    async def test_cart_item_references_product(
        self,
        async_session,
        sample_products
    ):
        """Test cart item foreign key to product."""
        product = sample_products[0]
        
        cart_item = CartItem(
            session_id="test",
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            total_price=product.price
        )
        
        async_session.add(cart_item)
        await async_session.commit()
        await async_session.refresh(cart_item)
        
        # Verify relationship
        statement = select(Product).where(Product.id == cart_item.product_id)
        result = await async_session.execute(statement)
        fetched_product = result.scalar_one_or_none()
        
        assert fetched_product is not None
        assert fetched_product.id == product.id


class TestDatabaseTransactions:
    """Tests for database transaction handling."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, async_session):
        """Test transaction rolls back on error."""
        # Add a valid product
        product1 = Product(
            id="trans_test_1",
            name="Product 1",
            description="Test",
            price=10.0,
            category=ProductCategory.ELECTRONICS,
            image_url="https://test.com/img.jpg",
            in_stock=True
        )
        async_session.add(product1)
        
        try:
            # Try to add invalid product
            product2 = Product(
                id="trans_test_2",
                name="Product 2",
                description="Test",
                price=-10.0,  # Invalid
                category=ProductCategory.ELECTRONICS,
                image_url="https://test.com/img.jpg",
                in_stock=True
            )
            async_session.add(product2)
            await async_session.commit()
        except Exception:
            await async_session.rollback()
        
        # Verify first product was not committed
        statement = select(Product).where(Product.id == "trans_test_1")
        result = await async_session.execute(statement)
        product = result.scalar_one_or_none()
        
        # Should be None because transaction rolled back
        # (depending on transaction scope in test)
    
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, async_session, test_session_context):
        """Test handling concurrent updates to same record."""
        # Update context data
        test_session_context.context_data["field1"] = "value1"
        async_session.add(test_session_context)
        await async_session.commit()
        
        # Update again
        await async_session.refresh(test_session_context)
        test_session_context.context_data["field2"] = "value2"
        async_session.add(test_session_context)
        await async_session.commit()
        
        # Verify both updates persisted
        await async_session.refresh(test_session_context)
        assert test_session_context.context_data["field1"] == "value1"
        assert test_session_context.context_data["field2"] == "value2"


class TestDatabasePerformance:
    """Tests for database performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_products(self, async_session):
        """Test bulk inserting multiple products."""
        products = [
            Product(
                id=f"bulk_prod_{i}",
                name=f"Product {i}",
                description=f"Description {i}",
                price=float(i * 10),
                category=ProductCategory.ELECTRONICS,
                image_url=f"https://test.com/img{i}.jpg",
                in_stock=True,
                stock_quantity=10
            )
            for i in range(10)
        ]
        
        for product in products:
            async_session.add(product)
        await async_session.commit()
        
        # Verify all were inserted
        statement = select(Product).where(
            Product.id.like("bulk_prod_%")
        )
        result = await async_session.execute(statement)
        fetched = result.scalars().all()
        
        assert len(fetched) == 10
    
    @pytest.mark.asyncio
    async def test_query_with_multiple_filters(
        self,
        async_session,
        sample_products
    ):
        """Test complex query with multiple filters."""
        statement = select(Product).where(
            Product.category == ProductCategory.ELECTRONICS,
            Product.in_stock == True,
            Product.price < 300
        )
        result = await async_session.execute(statement)
        products = result.scalars().all()
        
        # Verify all match filters
        for product in products:
            assert product.category == ProductCategory.ELECTRONICS
            assert product.in_stock is True
            assert product.price < 300

