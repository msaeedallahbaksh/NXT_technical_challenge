/**
 * Search Results Component
 * 
 * Displays product search results in a responsive grid.
 * Shows search metadata (query, count, category filter).
 */

import React from 'react';
import ProductCard, { ProductCardData } from './ProductCard';

interface SearchResultsProps {
  products: ProductCardData[];
  query?: string;
  category?: string;
  total_results?: number;
  onProductSelect?: (productId: string) => void;
  onAddToCart?: (productId: string, quantity: number) => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  products,
  query,
  category,
  total_results,
  onProductSelect,
  onAddToCart
}) => {
  if (!products || products.length === 0) {
    return (
      <div className="border rounded-lg p-8 bg-gray-50 text-center">
        <div className="text-4xl mb-3">🔍</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Products Found
        </h3>
        <p className="text-sm text-gray-600">
          {query ? (
            <>We couldn't find any products matching "<strong>{query}</strong>"</>
          ) : (
            <>No products available at the moment</>
          )}
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-6 bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Search Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            🔍 Search Results
          </h3>
          <span className="text-sm text-gray-600">
            {total_results || products.length} result{(total_results || products.length) !== 1 ? 's' : ''}
          </span>
        </div>
        
        {/* Search Metadata */}
        <div className="flex flex-wrap gap-2">
          {query && (
            <div className="bg-white px-3 py-1 rounded-full text-sm">
              <span className="text-gray-600">Query:</span>{' '}
              <span className="font-medium text-gray-900">{query}</span>
            </div>
          )}
          {category && (
            <div className="bg-white px-3 py-1 rounded-full text-sm">
              <span className="text-gray-600">Category:</span>{' '}
              <span className="font-medium text-gray-900 capitalize">{category}</span>
            </div>
          )}
        </div>
      </div>

      {/* Product Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onViewDetails={onProductSelect}
            onAddToCart={onAddToCart}
          />
        ))}
      </div>

      {/* Footer Note */}
      {products.length > 0 && (
        <div className="mt-4 text-center text-xs text-gray-500">
          Click "View Details" for more information or "Add to Cart" to purchase
        </div>
      )}
    </div>
  );
};

export default SearchResults;

