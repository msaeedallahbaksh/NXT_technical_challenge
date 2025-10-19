/**
 * Message List Component - Displays chat messages
 * 
 * Renders different message types (user, assistant, function_call, error) with
 * appropriate styling and layout. User messages appear on the right,
 * AI messages on the left.
 */

import React from 'react';
import { Message } from '../hooks/useSSEConnection';
import FunctionCallRenderer from './FunctionCallRenderer';

interface MessageListProps {
  messages: Message[];
  onInteraction?: (action: string, data: any) => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, onInteraction }) => {
  const renderMessage = (message: Message) => {
    switch (message.type) {
      case 'user':
        return (
          <div key={message.id} className="flex items-start justify-end">
            <div className="flex-1 flex justify-end">
              <div className="max-w-3xl">
                <div className="bg-blue-500 text-white rounded-lg px-4 py-2">
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
                <div className="text-xs text-gray-500 mt-1 text-right">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        );

      case 'assistant':
        return (
          <div key={message.id} className="flex items-start">
            <div className="flex-1 max-w-3xl">
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <p className="text-gray-900 whitespace-pre-wrap">{message.content}</p>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        );

      case 'function_call':
        return (
          <div key={message.id} className="flex items-start">
            <div className="flex-1 max-w-3xl">
              <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2">
                <p className="text-green-900 text-sm font-medium">
                  {message.content}
                </p>
                {/* Inline results under the same message (no function name, no icons) */}
                {message.function_call?.result?.success && message.function_call?.result?.data && (
                  <div className="mt-3">
                    <FunctionCallRenderer 
                      functionCall={message.function_call}
                      onInteraction={onInteraction}
                    />
                  </div>
                )}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        );

      case 'error':
        return (
          <div key={message.id} className="flex items-start">
            <div className="flex-1 max-w-3xl">
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2">
                <p className="text-red-900 font-medium text-sm">Error</p>
                <p className="text-red-700 text-sm mt-1">{message.content}</p>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div key={message.id} className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-gray-600 text-xs">?</span>
            </div>
            <div className="flex-1 max-w-2xl">
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <p className="text-gray-700">{message.content}</p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="space-y-4">
      {messages.map(renderMessage)}
    </div>
  );
};

export default MessageList;