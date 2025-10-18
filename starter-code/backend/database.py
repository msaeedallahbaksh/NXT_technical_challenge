"""
Database configuration and session management.

This module handles async database connections using SQLModel and PostgreSQL.
"""

import os
from typing import AsyncGenerator

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/assistant"
)

# Create async engine
engine: AsyncEngine = AsyncEngine(
    create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "false").lower() == "true")
)


async def init_db():
    """Initialize database tables and seed sample data."""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from models import Product, SessionContext, SearchContext, CartItem, ProductCategory
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Seed sample data
    await seed_sample_data()


async def seed_sample_data():
    """Seed database with sample products."""
    from models import Product, ProductCategory
    from sqlmodel import select
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if products already exist
        result = await session.execute(select(Product).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Sample products already exist, skipping seed")
            return
        
        print("🌱 Seeding sample products...")
        
        # Sample products
        sample_products = [
            Product(
                id="prod_001",
                name="Wireless Bluetooth Headphones",
                description="Premium noise-cancelling wireless headphones with 30-hour battery life",
                price=199.99,
                category=ProductCategory.ELECTRONICS,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=25,
                rating=4.5,
                reviews_count=1247,
                specifications={"brand": "TechSound", "model": "TS-1000", "warranty": "2 years"},
                features=["Active Noise Cancellation", "Quick Charge", "Voice Assistant Compatible"]
            ),
            Product(
                id="prod_002",
                name="Smartphone Protective Case",
                description="Ultra-slim transparent case with wireless charging support",
                price=29.99,
                category=ProductCategory.ELECTRONICS,
                image_url="https://images.unsplash.com/photo-1556656793-08538906a9f8?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=150,
                rating=4.2,
                reviews_count=892,
                specifications={"material": "TPU + PC", "compatibility": "iPhone 14/15"},
                features=["Wireless Charging Compatible", "Drop Protection", "Crystal Clear"]
            ),
            Product(
                id="prod_003",
                name="100% Organic Cotton T-Shirt",
                description="Comfortable premium cotton t-shirt in multiple colors",
                price=24.99,
                category=ProductCategory.CLOTHING,
                image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=200,
                rating=4.0,
                reviews_count=3456,
                specifications={"material": "100% Organic Cotton", "care": "Machine Washable"},
                features=["100% Organic Cotton", "Pre-shrunk", "Available in 12 Colors"]
            ),
            Product(
                id="prod_004",
                name="Smart Home Security Camera",
                description="AI-powered security camera with motion detection",
                price=149.99,
                category=ProductCategory.ELECTRONICS,
                image_url="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=45,
                rating=4.7,
                reviews_count=567,
                specifications={"resolution": "4K Ultra HD", "night_vision": "Up to 30ft"},
                features=["4K Ultra HD Recording", "AI Motion Detection", "Two-Way Audio"]
            ),
            Product(
                id="prod_005",
                name="Ergonomic Office Chair",
                description="Premium ergonomic chair with lumbar support",
                price=299.99,
                category=ProductCategory.HOME,
                image_url="https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=30,
                rating=4.6,
                reviews_count=234,
                specifications={"material": "Mesh + Steel", "weight_capacity": "300lbs"},
                features=["Lumbar Support", "Breathable Mesh", "Height Adjustable"]
            ),
            Product(
                id="prod_006",
                name="Bestselling Mystery Novel",
                description="Gripping psychological thriller",
                price=14.99,
                category=ProductCategory.BOOKS,
                image_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=75,
                rating=4.4,
                reviews_count=12890,
                specifications={"pages": 342, "publisher": "Mystery House"},
                features=["Bestseller List", "Award Winner", "Page Turner"]
            ),
            Product(
                id="prod_007",
                name="Professional Tennis Racket",
                description="Tournament-grade tennis racket",
                price=189.99,
                category=ProductCategory.SPORTS,
                image_url="https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=20,
                rating=4.8,
                reviews_count=445,
                specifications={"weight": "300g", "head_size": "98 sq in"},
                features=["Professional Grade", "Carbon Fiber Frame", "Tournament Approved"]
            ),
            Product(
                id="prod_008",
                name="Natural Face Moisturizer",
                description="Hydrating face cream with organic ingredients",
                price=39.99,
                category=ProductCategory.BEAUTY,
                image_url="https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=120,
                rating=4.3,
                reviews_count=2156,
                specifications={"size": "50ml", "skin_type": "All Types"},
                features=["Organic Ingredients", "Cruelty-Free", "SPF Protection"]
            ),
            Product(
                id="prod_009",
                name="Gaming Mechanical Keyboard",
                description="RGB backlit mechanical keyboard with programmable keys",
                price=129.99,
                category=ProductCategory.ELECTRONICS,
                image_url="https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=60,
                rating=4.5,
                reviews_count=1789,
                specifications={"switch_type": "Cherry MX Blue", "backlight": "RGB"},
                features=["Mechanical Switches", "RGB Backlighting", "Programmable Keys"]
            ),
            Product(
                id="prod_010",
                name="Stainless Steel Water Bottle",
                description="Insulated water bottle - 24h cold / 12h hot",
                price=34.99,
                category=ProductCategory.HOME,
                image_url="https://images.unsplash.com/photo-1523362628745-0c100150b504?w=300&h=300&fit=crop",
                in_stock=True,
                stock_quantity=80,
                rating=4.1,
                reviews_count=3421,
                specifications={"capacity": "750ml", "material": "Stainless Steel"},
                features=["24h Cold / 12h Hot", "Leak-Proof Design", "BPA-Free"]
            )
        ]
        
        for product in sample_products:
            session.add(product)
        
        await session.commit()
        print(f"✅ Seeded {len(sample_products)} sample products")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()