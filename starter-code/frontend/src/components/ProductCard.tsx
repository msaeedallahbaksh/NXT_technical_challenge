/**
 * Product Card Component
 * 
 * Displays a single product with:
 * - Product image
 * - Name and description
 * - Price and rating
 * - Add to Cart button
 * - Stock status
 */

import React from 'react';

export interface ProductCardData {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  image_url: string;
  in_stock: boolean;
  rating?: number;
  reviews_count?: number;
}

interface ProductCardProps {
  product: ProductCardData;
  onAddToCart?: (productId: string, quantity: number) => void;
  onViewDetails?: (productId: string) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({ 
  product, 
  onAddToCart,
  onViewDetails 
}) => {
  const handleAddToCart = () => {
    if (onAddToCart && product.in_stock) {
      onAddToCart(product.id, 1);
    }
  };

  const handleViewDetails = () => {
    if (onViewDetails) {
      onViewDetails(product.id);
    }
  };

  return (
    <div className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow bg-white">
      {/* Product Image */}
      <div className="relative h-48 bg-gray-100 overflow-hidden">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback to placeholder if image fails to load
              e.currentTarget.src = `https://via.placeholder.com/300x200/e5e7eb/6b7280?text=${encodeURIComponent(product.category)}`;
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-4xl">📦</span>
          </div>
        )}
        
        {/* Stock Badge */}
        {!product.in_stock && (
          <div className="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded">
            Out of Stock
          </div>
        )}
        
        {/* Category Badge */}
        <div className="absolute top-2 left-2 bg-white bg-opacity-90 text-gray-700 text-xs px-2 py-1 rounded capitalize">
          {product.category}
        </div>
      </div>

      {/* Product Info */}
      <div className="p-4">
        {/* Name */}
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
          {product.name}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {product.description}
        </p>

        {/* Rating */}
        {product.rating && (
          <div className="flex items-center mb-2">
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <span
                  key={i}
                  className={`text-sm ${
                    i < Math.floor(product.rating || 0)
                      ? 'text-yellow-400'
                      : 'text-gray-300'
                  }`}
                >
                  ★
                </span>
              ))}
            </div>
            <span className="text-xs text-gray-500 ml-2">
              ({product.reviews_count || 0} reviews)
            </span>
          </div>
        )}

        {/* Price */}
        <div className="text-2xl font-bold text-gray-900 mb-3">
          ${product.price.toFixed(2)}
        </div>

        {/* Actions */}
        <div className="flex space-x-2">
          <button
            onClick={handleViewDetails}
            className="flex-1 px-4 py-2 border border-blue-500 text-blue-500 rounded hover:bg-blue-50 transition-colors text-sm font-medium"
          >
            View Details
          </button>
          <button
            onClick={handleAddToCart}
            disabled={!product.in_stock}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {product.in_stock ? 'Add to Cart' : 'Out of Stock'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;

