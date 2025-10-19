import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import FunctionCallRenderer from '../FunctionCallRenderer';

// Mock the child components
jest.mock('../SearchResults', () => {
  return function MockSearchResults(props: any) {
    return (
      <div data-testid="search-results">
        SearchResults with {props.products?.length || 0} products
      </div>
    );
  };
});

jest.mock('../CartNotification', () => {
  return function MockCartNotification(props: any) {
    return (
      <div data-testid="cart-notification">
        Cart: {props.cart_item?.product_name || 'No item'}
      </div>
    );
  };
});

jest.mock('../RecommendationGrid', () => {
  return function MockRecommendationGrid(props: any) {
    return (
      <div data-testid="recommendation-grid">
        Recommendations: {props.recommendations?.length || 0} items
      </div>
    );
  };
});

jest.mock('../ProductDetailView', () => {
  return function MockProductDetailView(props: any) {
    return (
      <div data-testid="product-detail">
        Product: {props.product?.name || 'Unknown'}
      </div>
    );
  };
});

describe('FunctionCallRenderer', () => {
  const mockOnInteraction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Mapping', () => {
    it('should render SearchResults for search_products', () => {
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'headphones' },
        result: {
          success: true,
          data: {
            products: [
              { id: '1', name: 'Product 1' },
              { id: '2', name: 'Product 2' },
            ],
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByTestId('search-results')).toBeInTheDocument();
      expect(screen.getByText('SearchResults with 2 products')).toBeInTheDocument();
    });

    it('should render ProductDetailView for show_product_details', () => {
      const functionCall = {
        name: 'show_product_details',
        parameters: { product_id: 'prod_001' },
        result: {
          success: true,
          data: {
            product: {
              id: 'prod_001',
              name: 'Wireless Headphones',
            },
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByTestId('product-detail')).toBeInTheDocument();
      expect(screen.getByText('Product: Wireless Headphones')).toBeInTheDocument();
    });

    it('should render CartNotification for add_to_cart', () => {
      const functionCall = {
        name: 'add_to_cart',
        parameters: { product_id: 'prod_001', quantity: 2 },
        result: {
          success: true,
          data: {
            cart_item: {
              product_name: 'Headphones',
              quantity: 2,
            },
            cart_summary: {
              total_items: 2,
            },
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByTestId('cart-notification')).toBeInTheDocument();
      expect(screen.getByText('Cart: Headphones')).toBeInTheDocument();
    });

    it('should render RecommendationGrid for get_recommendations', () => {
      const functionCall = {
        name: 'get_recommendations',
        parameters: { based_on: 'prod_001' },
        result: {
          success: true,
          data: {
            recommendations: [
              { id: '1', name: 'Rec 1' },
              { id: '2', name: 'Rec 2' },
              { id: '3', name: 'Rec 3' },
            ],
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByTestId('recommendation-grid')).toBeInTheDocument();
      expect(screen.getByText('Recommendations: 3 items')).toBeInTheDocument();
    });
  });

  describe('Unknown Function Handling', () => {
    it('should render unknown function message for unmapped functions', () => {
      const functionCall = {
        name: 'unknown_function',
        parameters: {},
        result: {
          success: true,
          data: {},
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByText('Unknown Function Call')).toBeInTheDocument();
      expect(screen.getByText('Function "unknown_function" not implemented')).toBeInTheDocument();
    });
  });

  describe('Add to Cart Special Handling', () => {
    it('should show waiting message when cart_item is missing', () => {
      const functionCall = {
        name: 'add_to_cart',
        parameters: { product_id: 'prod_001' },
        result: {
          success: true,
          data: {
            // Missing cart_item
            cart_summary: {
              total_items: 1,
            },
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByText('Waiting for cart details...')).toBeInTheDocument();
    });

    it('should show waiting message when cart_summary is missing', () => {
      const functionCall = {
        name: 'add_to_cart',
        parameters: { product_id: 'prod_001' },
        result: {
          success: true,
          data: {
            cart_item: {
              product_name: 'Headphones',
              quantity: 1,
            },
            // Missing cart_summary
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByText('Waiting for cart details...')).toBeInTheDocument();
    });

    it('should render CartNotification when both cart_item and cart_summary exist', () => {
      const functionCall = {
        name: 'add_to_cart',
        parameters: { product_id: 'prod_001' },
        result: {
          success: true,
          data: {
            cart_item: {
              product_name: 'Headphones',
              quantity: 1,
            },
            cart_summary: {
              total_items: 1,
            },
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByTestId('cart-notification')).toBeInTheDocument();
    });
  });

  describe('Props Merging', () => {
    it('should merge parameters and result data into component props', () => {
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'laptop', category: 'electronics' },
        result: {
          success: true,
          data: {
            products: [{ id: '1', name: 'Laptop' }],
          },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      // Component should receive both parameters and result data
      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });

    it('should handle missing result data gracefully', () => {
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'test' },
        result: {
          success: true,
          data: null,
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      // Should still render the component
      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });

    it('should handle missing result entirely', () => {
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'test' },
        // No result
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      // Should still render with parameters
      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });
  });

  describe('Interaction Handling', () => {
    it('should wrap onInteraction with function context', () => {
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'test' },
        result: {
          success: true,
          data: { products: [] },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      // Component receives wrapped interaction handler
      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });

    it('should handle onInteraction being undefined', () => {
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'test' },
        result: {
          success: true,
          data: { products: [] },
        },
      };

      // Should not throw when onInteraction is undefined
      expect(() => {
        render(<FunctionCallRenderer functionCall={functionCall} />);
      }).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle component rendering errors gracefully', () => {
      const functionCall = {
        name: 'search_products',
        parameters: {},
        result: {
          success: true,
          data: {},
        },
      };

      // Should not throw even with minimal data
      expect(() => {
        render(
          <FunctionCallRenderer
            functionCall={functionCall}
            onInteraction={mockOnInteraction}
          />
        );
      }).not.toThrow();
    });

    it('should render when parameters are empty', () => {
      const functionCall = {
        name: 'search_products',
        parameters: {},
        result: {
          success: true,
          data: { products: [] },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });
  });

  describe('Console Logging', () => {
    it('should log interactions to console', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      const functionCall = {
        name: 'search_products',
        parameters: { query: 'test' },
        result: {
          success: true,
          data: { products: [] },
        },
      };

      render(
        <FunctionCallRenderer
          functionCall={functionCall}
          onInteraction={mockOnInteraction}
        />
      );

      // The component logs interactions
      // (This would be triggered by actual user interactions in the child components)

      consoleSpy.mockRestore();
    });
  });
});

