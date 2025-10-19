/**
 * Function Call Renderer - Dynamically renders components based on AI function calls
 * 
 * This is the "magic" component that converts AI function calls into React UI components.
 * When the AI calls a function like "search_products", this component renders it as a 
 * visual product grid instead of just JSON data.
 */

import React from 'react';
import SearchResults from './SearchResults';
import CartNotification from './CartNotification';
import RecommendationGrid from './RecommendationGrid';
import ProductDetailView from './ProductDetailView';

interface FunctionCall {
  name: string;
  parameters: Record<string, any>;
  result?: any;
}

interface FunctionCallRendererProps {
  functionCall: FunctionCall;
  onInteraction?: (action: string, data: any) => void;
}

// Function call mapping - Maps AI function names to React components
const FunctionComponents: Record<string, React.ComponentType<any>> = {
  search_products: SearchResults,
  show_product_details: ProductDetailView,
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
        {/* Hide verbose parameters by default for a cleaner UI */}
      </div>
    );
  }

  // Handle different function call types
  const handleInteraction = (action: string, data: any) => {
    onInteraction?.(action, { function: name, ...data });
  };

  // Render the appropriate component with function call data
  try {
    // Only render when we have a successful result or required props
    const safeProps = {
      ...(parameters || {}),
      ...((result && result.success && result.data) ? result.data : {}),
    };

    // Guard for add_to_cart shape to avoid crashes
    if (name === 'add_to_cart') {
      const cartItem = safeProps.cart_item;
      const cartSummary = safeProps.cart_summary;
      if (!cartItem || !cartSummary) {
        return (
          <div className="border rounded-lg p-4 bg-yellow-50">
            <h3 className="font-medium text-yellow-900 mb-2">Add to Cart</h3>
            <p className="text-sm text-yellow-700">Waiting for cart details...</p>
          </div>
        );
      }
    }

    return (
      <div className="mt-3">
        <Component
          {...safeProps}
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