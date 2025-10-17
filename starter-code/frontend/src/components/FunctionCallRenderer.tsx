/**
 * Function Call Renderer - Dynamically renders components based on AI function calls
 * 
 * TODO: This is a key component that maps AI function calls to React components.
 * Implement the component mapping and rendering logic.
 */

import React from 'react';

interface FunctionCall {
  name: string;
  parameters: Record<string, any>;
  result?: any;
}

interface FunctionCallRendererProps {
  functionCall: FunctionCall;
  onInteraction?: (action: string, data: any) => void;
}

// TODO: Implement these components or create placeholder components
const SearchResults: React.FC<any> = ({ products, onProductSelect }) => (
  <div className="border rounded-lg p-4 bg-blue-50">
    <h3 className="font-medium text-blue-900 mb-2">Search Results</h3>
    <p className="text-sm text-blue-700">
      TODO: Implement SearchResults component - Found {products?.length || 0} products
    </p>
  </div>
);

const ProductCard: React.FC<any> = ({ product, onAddToCart }) => (
  <div className="border rounded-lg p-4 bg-green-50">
    <h3 className="font-medium text-green-900 mb-2">Product Details</h3>
    <p className="text-sm text-green-700">
      TODO: Implement ProductCard component - {product?.name || 'Product'}
    </p>
  </div>
);

const CartNotification: React.FC<any> = ({ cartItem }) => (
  <div className="border rounded-lg p-4 bg-purple-50">
    <h3 className="font-medium text-purple-900 mb-2">Added to Cart</h3>
    <p className="text-sm text-purple-700">
      TODO: Implement CartNotification component - {cartItem?.product_name || 'Item'}
    </p>
  </div>
);

const RecommendationGrid: React.FC<any> = ({ recommendations }) => (
  <div className="border rounded-lg p-4 bg-orange-50">
    <h3 className="font-medium text-orange-900 mb-2">Recommendations</h3>
    <p className="text-sm text-orange-700">
      TODO: Implement RecommendationGrid component - {recommendations?.length || 0} recommendations
    </p>
  </div>
);

// Function call mapping - Maps AI function names to React components
const FunctionComponents: Record<string, React.ComponentType<any>> = {
  search_products: SearchResults,
  show_product_details: ProductCard,
  add_to_cart: CartNotification,
  get_recommendations: RecommendationGrid
};

const FunctionCallRenderer: React.FC<FunctionCallRendererProps> = ({
  functionCall,
  onInteraction
}) => {
  const { name, parameters, result } = functionCall;
  
  // Get the component for this function call
  const Component = FunctionComponents[name];
  
  if (!Component) {
    return (
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="font-medium text-gray-900 mb-2">Unknown Function Call</h3>
        <p className="text-sm text-gray-600">
          Function "{name}" not implemented
        </p>
        <div className="mt-2 text-xs text-gray-500">
          Parameters: {JSON.stringify(parameters, null, 2)}
        </div>
      </div>
    );
  }

  // Handle different function call types
  const handleInteraction = (action: string, data: any) => {
    console.log('Function interaction:', { function: name, action, data });
    onInteraction?.(action, { function: name, ...data });
  };

  // Render the appropriate component with function call data
  try {
    return (
      <div className="my-4">
        <Component
          {...parameters}
          {...(result?.data || {})}
          onInteraction={handleInteraction}
          onProductSelect={(id: string) => handleInteraction('select_product', { product_id: id })}
          onAddToCart={(id: string, quantity: number) => handleInteraction('add_to_cart', { product_id: id, quantity })}
        />
      </div>
    );
  } catch (error) {
    console.error('Error rendering function call component:', error);
    
    return (
      <div className="border rounded-lg p-4 bg-red-50">
        <h3 className="font-medium text-red-900 mb-2">Render Error</h3>
        <p className="text-sm text-red-700">
          Failed to render component for function "{name}"
        </p>
        <div className="mt-2 text-xs text-red-600">
          {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </div>
    );
  }
};

export default FunctionCallRenderer;