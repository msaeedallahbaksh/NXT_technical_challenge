-- Complete database initialization with table creation and sample data
-- This file creates all necessary tables AND populates them with sample data

-- Enable UUID extension (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types for categories
DO $$ BEGIN
    CREATE TYPE productcategory AS ENUM ('electronics', 'clothing', 'home', 'books', 'sports', 'beauty', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create Product table
CREATE TABLE IF NOT EXISTS product (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT NOT NULL,
    long_description TEXT,
    price FLOAT NOT NULL CHECK (price >= 0),
    category productcategory NOT NULL,
    image_url VARCHAR NOT NULL,
    additional_images JSON DEFAULT '[]',
    in_stock BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    rating FLOAT CHECK (rating >= 0 AND rating <= 5),
    reviews_count INTEGER DEFAULT 0 CHECK (reviews_count >= 0),
    specifications JSON DEFAULT '{}',
    features JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_product_name ON product(name);
CREATE INDEX IF NOT EXISTS idx_product_category ON product(category);
CREATE INDEX IF NOT EXISTS idx_product_in_stock ON product(in_stock);

-- Create SessionContext table
CREATE TABLE IF NOT EXISTS sessioncontext (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR UNIQUE NOT NULL,
    context_data JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessioncontext_session_id ON sessioncontext(session_id);

-- Create SearchContext table
CREATE TABLE IF NOT EXISTS searchcontext (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    search_query VARCHAR NOT NULL,
    results JSON NOT NULL,
    category VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_searchcontext_session_id ON searchcontext(session_id);

-- Create CartItem table
CREATE TABLE IF NOT EXISTS cartitem (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    product_id VARCHAR NOT NULL REFERENCES product(id),
    quantity INTEGER DEFAULT 1 CHECK (quantity >= 1),
    unit_price FLOAT NOT NULL CHECK (unit_price >= 0),
    total_price FLOAT NOT NULL CHECK (total_price >= 0),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cartitem_session_id ON cartitem(session_id);

-- Insert sample products
INSERT INTO product (id, name, description, price, category, image_url, in_stock, stock_quantity, rating, reviews_count, specifications, features) VALUES
    ('prod_001', 'Wireless Bluetooth Headphones', 'Premium noise-cancelling wireless headphones with 30-hour battery life', 199.99, 'electronics', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop', true, 25, 4.5, 1247, '{"brand": "TechSound", "model": "TS-1000", "warranty": "2 years", "connectivity": "Bluetooth 5.0", "battery_life": "30 hours", "weight": "250g"}', '["Active Noise Cancellation", "Quick Charge (10min = 5hours)", "Voice Assistant Compatible", "Foldable Design"]'),
    
    ('prod_002', 'Smartphone Protective Case', 'Ultra-slim transparent case with wireless charging support and drop protection', 29.99, 'electronics', 'https://images.unsplash.com/photo-1556656793-08538906a9f8?w=300&h=300&fit=crop', true, 150, 4.2, 892, '{"material": "TPU + PC", "compatibility": "iPhone 14/15", "wireless_charging": true, "drop_protection": "10ft", "thickness": "1.2mm"}', '["Wireless Charging Compatible", "Military Grade Drop Protection", "Crystal Clear", "Precise Cutouts"]'),
    
    ('prod_003', '100% Organic Cotton T-Shirt', 'Comfortable premium cotton t-shirt available in multiple colors and sizes', 24.99, 'clothing', 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=300&h=300&fit=crop', true, 200, 4.0, 3456, '{"material": "100% Organic Cotton", "care": "Machine Washable", "fit": "Regular", "weight": "180gsm", "origin": "USA"}', '["100% Organic Cotton", "Pre-shrunk", "Available in 12 Colors", "Sustainable Production"]'),
    
    ('prod_004', 'Smart Home Security Camera', 'AI-powered security camera with motion detection and night vision', 149.99, 'electronics', 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300&h=300&fit=crop', true, 45, 4.7, 567, '{"resolution": "4K Ultra HD", "field_of_view": "130 degrees", "night_vision": "Up to 30ft", "storage": "Cloud + Local", "ai_detection": true}', '["4K Ultra HD Recording", "AI Motion Detection", "Two-Way Audio", "Weather Resistant", "Mobile App Control"]'),
    
    ('prod_005', 'Ergonomic Office Chair', 'Premium ergonomic chair with lumbar support and adjustable height', 299.99, 'home', 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=300&h=300&fit=crop', true, 30, 4.6, 234, '{"material": "Mesh + Steel", "weight_capacity": "300lbs", "height_adjustment": "17-21 inches", "warranty": "5 years", "assembly": "Required"}', '["Lumbar Support", "Breathable Mesh", "360° Swivel", "Height Adjustable", "Armrest Support"]'),
    
    ('prod_006', 'Bestselling Mystery Novel', 'Gripping psychological thriller that kept readers turning pages all night', 14.99, 'books', 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=300&fit=crop', true, 75, 4.4, 12890, '{"pages": 342, "publisher": "Mystery House", "publication_year": 2023, "language": "English", "format": "Paperback"}', '["Bestseller List", "Award Winner", "Book Club Favorite", "Page Turner"]'),
    
    ('prod_007', 'Professional Tennis Racket', 'Tournament-grade tennis racket used by professional players worldwide', 189.99, 'sports', 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=300&h=300&fit=crop', true, 20, 4.8, 445, '{"weight": "300g", "head_size": "98 sq in", "string_pattern": "16x19", "balance": "310mm", "grip_size": "4 1/4"}', '["Professional Grade", "Carbon Fiber Frame", "Shock Absorption", "Tournament Approved"]'),
    
    ('prod_008', 'Natural Face Moisturizer', 'Hydrating face cream with organic ingredients for all skin types', 39.99, 'beauty', 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=300&h=300&fit=crop', true, 120, 4.3, 2156, '{"size": "50ml", "skin_type": "All Types", "spf": "SPF 15", "ingredients": "Organic", "cruelty_free": true}', '["Organic Ingredients", "Cruelty-Free", "SPF Protection", "Dermatologist Tested", "Fragrance-Free"]'),
    
    ('prod_009', 'Gaming Mechanical Keyboard', 'RGB backlit mechanical keyboard with programmable keys for gaming', 129.99, 'electronics', 'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=300&h=300&fit=crop', true, 60, 4.5, 1789, '{"switch_type": "Cherry MX Blue", "backlight": "RGB", "connectivity": "USB-C", "key_rollover": "N-Key", "software": "Programmable"}', '["Mechanical Switches", "RGB Backlighting", "Programmable Keys", "Gaming Mode", "Anti-Ghosting"]'),
    
    ('prod_010', 'Stainless Steel Water Bottle', 'Insulated water bottle that keeps drinks cold for 24 hours or hot for 12 hours', 34.99, 'home', 'https://images.unsplash.com/photo-1523362628745-0c100150b504?w=300&h=300&fit=crop', true, 80, 4.1, 3421, '{"capacity": "750ml", "material": "Stainless Steel", "insulation": "Double Wall", "leak_proof": true, "bpa_free": true}', '["24h Cold / 12h Hot", "Leak-Proof Design", "BPA-Free", "Wide Mouth Opening", "Dishwasher Safe"]')
ON CONFLICT (id) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database initialized with % products', (SELECT COUNT(*) FROM product);
END $$;

