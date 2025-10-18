/**
 * Cart Notification Component
 * 
 * Displays a success message when a product is added to cart.
 * Shows cart summary and next actions.
 */

import React from 'react';

interface CartNotificationProps {
  cart_item: {
    id: string | number;
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
  };
  cart_summary: {
    total_items: number;
    total_products: number;
    subtotal: number;
    estimated_tax: number;
    estimated_total: number;
  };
}

const CartNotification: React.FC<CartNotificationProps> = ({
  cart_item,
  cart_summary
}) => {
  return (
    <div className="border-2 border-green-300 rounded-lg p-6 bg-gradient-to-br from-green-50 to-emerald-50">
      {/* Success Header */}
      <div className="flex items-center mb-4">
        <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center mr-3">
          <span className="text-white text-xl">✓</span>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-green-900">
            Added to Cart!
          </h3>
          <p className="text-sm text-green-700">
            Item successfully added to your shopping cart
          </p>
        </div>
      </div>

      {/* Cart Item Details */}
      <div className="bg-white rounded-lg p-4 mb-4">
        <div className="flex justify-between items-start mb-2">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900">{cart_item.product_name}</h4>
            <p className="text-sm text-gray-600">Product ID: {cart_item.product_id}</p>
          </div>
          <div className="text-right">
            <p className="font-semibold text-gray-900">${cart_item.total_price.toFixed(2)}</p>
            <p className="text-xs text-gray-600">${cart_item.unit_price.toFixed(2)} × {cart_item.quantity}</p>
          </div>
        </div>
      </div>

      {/* Cart Summary */}
      <div className="bg-white rounded-lg p-4 space-y-2">
        <h4 className="font-medium text-gray-900 mb-3">Cart Summary</h4>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Items in Cart:</span>
          <span className="font-medium text-gray-900">{cart_summary.total_items} items ({cart_summary.total_products} products)</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Subtotal:</span>
          <span className="font-medium text-gray-900">${cart_summary.subtotal.toFixed(2)}</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Estimated Tax:</span>
          <span className="font-medium text-gray-900">${cart_summary.estimated_tax.toFixed(2)}</span>
        </div>
        
        <div className="border-t pt-2 mt-2">
          <div className="flex justify-between">
            <span className="font-semibold text-gray-900">Total:</span>
            <span className="font-bold text-lg text-green-600">${cart_summary.estimated_total.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Action Hint */}
      <div className="mt-4 text-center text-sm text-gray-600">
        💡 Continue shopping or ask me to show your cart details
      </div>
    </div>
  );
};

export default CartNotification;

