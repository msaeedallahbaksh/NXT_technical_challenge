"""
Product service for managing product catalog operations.

This service handles product search, details, and recommendations.
"""

from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from models import Product, ProductCategory


class ProductService:
    """Service for product operations."""
    
    async def search_products(
        self,
        query: str,
        category: Optional[ProductCategory] = None,
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> List[Product]:
        """Search products by query and category."""
        
        if not session:
            # For the challenge, you'll need to inject the session
            # This is a placeholder implementation
            return await self._mock_search_products(query, category, limit)
        
        # Build query
        statement = select(Product).where(Product.in_stock)
        
        # Add text search
        if query:
            statement = statement.where(
                Product.name.contains(query) | 
                Product.description.contains(query)
            )
        
        # Add category filter
        if category:
            statement = statement.where(Product.category == category)
        
        # Add limit
        statement = statement.limit(limit)
        
        result = await session.execute(statement)
        return result.scalars().all()
    
    async def get_product_by_id(
        self,
        product_id: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[Product]:
        """Get product by ID."""
        
        if not session:
            return await self._mock_get_product(product_id)
        
        statement = select(Product).where(Product.id == product_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_recommendations(
        self,
        based_on_product_id: str,
        limit: int = 5,
        session: Optional[AsyncSession] = None
    ) -> List[Product]:
        """Get product recommendations."""
        
        if not session:
            return await self._mock_get_recommendations(based_on_product_id, limit)
        
        # Get the base product
        base_product = await self.get_product_by_id(based_on_product_id, session)
        if not base_product:
            return []
        
        # Find similar products (same category, different product)
        statement = select(Product).where(
            Product.category == base_product.category,
            Product.id != base_product.id,
            Product.in_stock
        ).limit(limit)
        
        result = await session.execute(statement)
        return result.scalars().all()
    
    # Mock implementations for development
    async def _mock_search_products(
        self,
        query: str,
        category: Optional[ProductCategory],
        limit: int
    ) -> List[Product]:
        """Mock product search for development."""
        
        mock_products = [
            Product(
                id="prod_001",
                name="Wireless Bluetooth Headphones",
                description="High-quality wireless headphones with noise cancellation",
                price=199.99,
                category=ProductCategory.ELECTRONICS,
                image_url="https://via.placeholder.com/300x300?text=Headphones",
                in_stock=True,
                stock_quantity=25,
                rating=4.5,
                reviews_count=156,
                features=["Noise Cancellation", "30h Battery", "Quick Charge"]
            ),
            Product(
                id="prod_002", 
                name="Smartphone Case",
                description="Protective case for smartphones with wireless charging support",
                price=29.99,
                category=ProductCategory.ELECTRONICS,
                image_url="https://via.placeholder.com/300x300?text=Phone+Case",
                in_stock=True,
                stock_quantity=50,
                rating=4.2,
                reviews_count=89,
                features=["Wireless Charging", "Drop Protection", "Slim Design"]
            ),
            Product(
                id="prod_003",
                name="Cotton T-Shirt",
                description="Comfortable 100% cotton t-shirt in various colors",
                price=24.99,
                category=ProductCategory.CLOTHING,
                image_url="https://via.placeholder.com/300x300?text=T-Shirt",
                in_stock=True,
                stock_quantity=100,
                rating=4.0,
                reviews_count=234,
                features=["100% Cotton", "Machine Washable", "Various Colors"]
            )
        ]
        
        # Simple filtering by query
        filtered_products = []
        for product in mock_products:
            if query.lower() in product.name.lower() or query.lower() in product.description.lower():
                if not category or product.category == category:
                    filtered_products.append(product)
        
        return filtered_products[:limit]
    
    async def _mock_get_product(self, product_id: str) -> Optional[Product]:
        """Mock get product by ID."""
        
        mock_products = await self._mock_search_products("", None, 100)
        
        for product in mock_products:
            if product.id == product_id:
                return product
        
        return None
    
    async def _mock_get_recommendations(
        self,
        based_on_product_id: str,
        limit: int
    ) -> List[Product]:
        """Mock recommendations."""
        
        all_products = await self._mock_search_products("", None, 100)
        base_product = await self._mock_get_product(based_on_product_id)
        
        if not base_product:
            return []
        
        # Return products from same category
        recommendations = []
        for product in all_products:
            if (product.category == base_product.category and 
                product.id != base_product.id):
                recommendations.append(product)
        
        return recommendations[:limit]