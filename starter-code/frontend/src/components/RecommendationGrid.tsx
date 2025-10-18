/**
 * Recommendation Grid Component
 * 
 * Displays AI-recommended products based on user's current selection or browse history.
 * Shows why each product is recommended.
 */

import React from 'react';
import ProductCard, { ProductCardData } from './ProductCard';

interface Recommendation extends ProductCardData {
  similarity_score?: number;
  reason?: string;
}

interface RecommendationGridProps {
  recommendations: Recommendation[];
  recommendation_context?: {
    based_on_product?: string;
    based_on_category?: string;
    algorithm?: string;
    factors?: string[];
  };
  onProductSelect?: (productId: string) => void;
  onAddToCart?: (productId: string, quantity: number) => void;
}

const RecommendationGrid: React.FC<RecommendationGridProps> = ({
  recommendations,
  recommendation_context,
  onProductSelect,
  onAddToCart
}) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="border rounded-lg p-6 bg-gray-50 text-center">
        <div className="text-4xl mb-3">💡</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Recommendations Available
        </h3>
        <p className="text-sm text-gray-600">
          We don't have any recommendations at the moment
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-6 bg-gradient-to-br from-orange-50 to-amber-50">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center mb-2">
          <span className="text-2xl mr-2">💡</span>
          <h3 className="text-lg font-semibold text-gray-900">
            Recommended For You
          </h3>
        </div>

        {/* Context Information */}
        {recommendation_context && (
          <div className="bg-white rounded-lg p-3 mb-4">
            {recommendation_context.based_on_product && (
              <p className="text-sm text-gray-700 mb-1">
                <span className="font-medium">Based on:</span> {recommendation_context.based_on_product}
              </p>
            )}
            {recommendation_context.based_on_category && !recommendation_context.based_on_product && (
              <p className="text-sm text-gray-700 mb-1">
                <span className="font-medium">Category:</span> {recommendation_context.based_on_category}
              </p>
            )}
            {recommendation_context.algorithm && (
              <p className="text-xs text-gray-600">
                <span className="font-medium">Algorithm:</span> {recommendation_context.algorithm.replace('_', ' ')}
              </p>
            )}
            {recommendation_context.factors && recommendation_context.factors.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {recommendation_context.factors.map((factor, idx) => (
                  <span
                    key={idx}
                    className="inline-block bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded"
                  >
                    {factor}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Recommendations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.map((product, index) => (
          <div key={product.id} className="relative">
            {/* Similarity Badge */}
            {product.similarity_score && (
              <div className="absolute top-2 right-2 z-10 bg-orange-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                {(product.similarity_score * 100).toFixed(0)}% Match
              </div>
            )}

            <ProductCard
              product={product}
              onViewDetails={onProductSelect}
              onAddToCart={onAddToCart}
            />

            {/* Reason Badge */}
            {product.reason && (
              <div className="mt-2 text-xs text-center text-gray-600 bg-white px-2 py-1 rounded">
                {product.reason}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-4 text-center text-xs text-gray-600">
        These recommendations are personalized based on your browsing and preferences
      </div>
    </div>
  );
};

export default RecommendationGrid;

