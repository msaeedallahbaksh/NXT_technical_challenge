/**
 * Product Detail View Component
 * 
 * Displays comprehensive product information including:
 * - High-quality image gallery
 * - Long description
 * - Detailed specifications
 * - Feature list
 * - Reviews and ratings
 * - Add to cart functionality
 * - Related recommendations
 */

import React, { useState } from 'react';

interface ProductDetailViewProps {
  product: {
    id: string;
    name: string;
    description: string;
    long_description?: string;
    price: number;
    category: string;
    image_url: string;
    additional_images?: string[];
    in_stock: boolean;
    stock_quantity: number;
    rating?: number;
    reviews_count?: number;
    specifications?: Record<string, any>;
    features?: string[];
  };
  recommendations?: any[];
  onAddToCart?: (productId: string, quantity: number) => void;
  onProductSelect?: (productId: string) => void;
}

const ProductDetailView: React.FC<ProductDetailViewProps> = ({
  product,
  recommendations,
  onAddToCart,
  onProductSelect
}) => {
  const [selectedImage, setSelectedImage] = useState(product.image_url);
  const [quantity, setQuantity] = useState(1);

  const handleAddToCart = () => {
    if (onAddToCart && product.in_stock) {
      onAddToCart(product.id, quantity);
    }
  };

  const allImages = [product.image_url, ...(product.additional_images || [])].filter(Boolean);

  return (
    <div className="border rounded-lg overflow-hidden bg-white shadow-lg">
      {/* Main Product Section */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left: Images */}
          <div>
            {/* Main Image */}
            <div className="relative bg-gray-100 rounded-lg overflow-hidden mb-4" style={{ aspectRatio: '1/1' }}>
              <img
                src={selectedImage}
                alt={product.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = `https://via.placeholder.com/600x600/e5e7eb/6b7280?text=${encodeURIComponent(product.category)}`;
                }}
              />
              
              {/* Stock Badge */}
              {!product.in_stock && (
                <div className="absolute top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg font-semibold">
                  Out of Stock
                </div>
              )}
            </div>

            {/* Image Thumbnails */}
            {allImages.length > 1 && (
              <div className="grid grid-cols-4 gap-2">
                {allImages.map((img, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedImage(img)}
                    className={`relative bg-gray-100 rounded overflow-hidden border-2 transition-all ${
                      selectedImage === img ? 'border-blue-500' : 'border-transparent hover:border-gray-300'
                    }`}
                    style={{ aspectRatio: '1/1' }}
                  >
                    <img
                      src={img}
                      alt={`${product.name} view ${idx + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.src = `https://via.placeholder.com/150/e5e7eb/6b7280`;
                      }}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right: Product Info */}
          <div>
            {/* Category Badge */}
            <div className="text-sm text-blue-600 font-medium uppercase tracking-wide mb-2">
              {product.category}
            </div>

            {/* Product Name */}
            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              {product.name}
            </h1>

            {/* Rating */}
            {product.rating && (
              <div className="flex items-center mb-4">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <span
                      key={i}
                      className={`text-lg ${
                        i < Math.floor(product.rating || 0)
                          ? 'text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                <span className="ml-2 text-sm text-gray-600">
                  {product.rating?.toFixed(1)} ({product.reviews_count?.toLocaleString()} reviews)
                </span>
              </div>
            )}

            {/* Price */}
            <div className="mb-6">
              <div className="text-4xl font-bold text-gray-900">
                ${product.price.toFixed(2)}
              </div>
              {product.in_stock && (
                <div className="text-sm text-green-600 mt-1">
                  ✓ In Stock ({product.stock_quantity} available)
                </div>
              )}
            </div>

            {/* Short Description */}
            <p className="text-gray-700 mb-6 leading-relaxed">
              {product.description}
            </p>

            {/* Quantity Selector & Add to Cart */}
            {product.in_stock && (
              <div className="flex items-center space-x-4 mb-6">
                <div className="flex items-center border rounded-lg">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="px-4 py-2 text-gray-600 hover:bg-gray-100"
                  >
                    −
                  </button>
                  <input
                    type="number"
                    min="1"
                    max={product.stock_quantity}
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, Math.min(product.stock_quantity, parseInt(e.target.value) || 1)))}
                    className="w-16 text-center border-x py-2 focus:outline-none"
                  />
                  <button
                    onClick={() => setQuantity(Math.min(product.stock_quantity, quantity + 1))}
                    className="px-4 py-2 text-gray-600 hover:bg-gray-100"
                  >
                    +
                  </button>
                </div>
                <button
                  onClick={handleAddToCart}
                  className="flex-1 bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Add to Cart
                </button>
              </div>
            )}

            {!product.in_stock && (
              <button
                disabled
                className="w-full bg-gray-300 text-gray-600 px-8 py-3 rounded-lg font-semibold cursor-not-allowed"
              >
                Out of Stock
              </button>
            )}

            {/* Features */}
            {product.features && product.features.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-gray-900 mb-3">Key Features</h3>
                <ul className="space-y-2">
                  {product.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-blue-600 mr-2">✓</span>
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Long Description */}
        {product.long_description && (
          <div className="mt-8 pt-8 border-t">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Product Description</h2>
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">
              {product.long_description}
            </p>
          </div>
        )}

        {/* Specifications */}
        {product.specifications && Object.keys(product.specifications).length > 0 && (
          <div className="mt-8 pt-8 border-t">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Specifications</h2>
            <div className="bg-gray-50 rounded-lg overflow-hidden">
              <table className="w-full">
                <tbody>
                  {Object.entries(product.specifications).map(([key, value], idx) => (
                    <tr key={key} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-3 font-medium text-gray-900 capitalize w-1/3">
                        {key.replace(/_/g, ' ')}
                      </td>
                      <td className="px-6 py-3 text-gray-700">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Recommendations Section */}
      {recommendations && recommendations.length > 0 && (
        <div className="border-t bg-gray-50 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">You Might Also Like</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {recommendations.slice(0, 4).map((rec) => (
              <div
                key={rec.id}
                className="bg-white border rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => onProductSelect?.(rec.id)}
              >
                <div className="relative bg-gray-100" style={{ aspectRatio: '1/1' }}>
                  <img
                    src={rec.image_url}
                    alt={rec.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = `https://via.placeholder.com/300/e5e7eb/6b7280`;
                    }}
                  />
                </div>
                <div className="p-3">
                  <h3 className="font-medium text-gray-900 text-sm mb-1 line-clamp-2">
                    {rec.name}
                  </h3>
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-gray-900">
                      ${rec.price?.toFixed(2)}
                    </span>
                    {rec.rating && (
                      <div className="flex items-center text-xs">
                        <span className="text-yellow-400">★</span>
                        <span className="ml-1 text-gray-600">{rec.rating.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductDetailView;

