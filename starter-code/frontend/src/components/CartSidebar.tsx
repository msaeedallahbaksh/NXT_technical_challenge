/**
 * Cart Sidebar Component
 * 
 * Displays cart contents with:
 * - Items list with product image, name, quantity, price
 * - Remove item functionality
 * - Cart totals (subtotal, tax, total)
 * - Empty cart message
 */

import React, { useEffect, useState } from 'react';

interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  product_image?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

interface CartSummary {
  total_items: number;
  total_products: number;
  subtotal: number;
  estimated_tax: number;
  estimated_total: number;
}

interface CartSidebarProps {
  sessionId: string;
  onCartUpdate?: () => void;
}

const CartSidebar: React.FC<CartSidebarProps> = ({ sessionId, onCartUpdate }) => {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartSummary, setCartSummary] = useState<CartSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchCart = async () => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_URL}/api/cart/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch cart');
      }
      
      const data = await response.json();
      setCartItems(data.items || []);
      setCartSummary(data.summary || null);
    } catch (err) {
      console.error('Error fetching cart:', err);
      setError('Failed to load cart');
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (productId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/functions/remove_from_cart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to remove item');
      }

      // Refresh cart
      await fetchCart();
      onCartUpdate?.();
    } catch (err) {
      console.error('Error removing item:', err);
      setError('Failed to remove item');
    }
  };

  // Fetch cart on mount and when sessionId changes
  useEffect(() => {
    fetchCart();
  }, [sessionId]);

  // Polling every 5 seconds to catch updates from chat interactions
  useEffect(() => {
    const interval = setInterval(fetchCart, 5000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (loading && cartItems.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 h-full">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🛒 Your Cart</h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">🛒 Your Cart</h2>
        {cartSummary && cartSummary.total_items > 0 && (
          <span className="bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded-full">
            {cartSummary.total_items}
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Cart Items */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {cartItems.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-3">🛒</div>
            <p className="text-gray-500">Your cart is empty</p>
            <p className="text-sm text-gray-400 mt-2">
              Add items by chatting with the AI!
            </p>
          </div>
        ) : (
          cartItems.map((item) => (
            <div
              key={item.id}
              className="border rounded-lg p-3 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start space-x-3">
                {/* Product Image */}
                {item.product_image ? (
                  <img
                    src={item.product_image}
                    alt={item.product_name}
                    className="w-16 h-16 object-cover rounded"
                    onError={(e) => {
                      e.currentTarget.src = `https://via.placeholder.com/64/e5e7eb/6b7280?text=Product`;
                    }}
                  />
                ) : (
                  <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                    <span className="text-2xl">📦</span>
                  </div>
                )}

                {/* Item Details */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm line-clamp-2">
                    {item.product_name}
                  </h4>
                  <p className="text-xs text-gray-500 mt-1">
                    ${item.unit_price.toFixed(2)} × {item.quantity}
                  </p>
                  <p className="text-sm font-bold text-gray-900 mt-1">
                    ${item.total_price.toFixed(2)}
                  </p>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeItem(item.product_id)}
                  className="text-red-500 hover:text-red-700 p-1"
                  title="Remove from cart"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Cart Summary */}
      {cartSummary && cartSummary.total_items > 0 && (
        <div className="border-t pt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Subtotal:</span>
            <span className="font-medium text-gray-900">
              ${cartSummary.subtotal.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Est. Tax:</span>
            <span className="font-medium text-gray-900">
              ${cartSummary.estimated_tax.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between text-lg font-bold pt-2 border-t">
            <span>Total:</span>
            <span className="text-blue-600">
              ${cartSummary.estimated_total.toFixed(2)}
            </span>
          </div>
          
          <button className="w-full mt-4 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
            Checkout
          </button>
        </div>
      )}
    </div>
  );
};

export default CartSidebar;

