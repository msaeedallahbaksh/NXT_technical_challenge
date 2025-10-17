/**
 * Message List Component - Displays chat messages
 * 
 * TODO: Implement this component to display the list of chat messages
 * with proper styling and message type handling.
 */

import React from 'react';
import { Message } from '../hooks/useSSEConnection';

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  // TODO: Implement message rendering
  // - Handle different message types (user, assistant, function_call, error)
  // - Style messages appropriately
  // - Show timestamps
  // - Handle function call messages specially
  
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div key={message.id} className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-xs">
              {message.type === 'user' ? 'U' : 'AI'}
            </span>
          </div>
          <div className="flex-1">
            <div className="bg-gray-100 rounded-lg px-3 py-2">
              <p>{message.content}</p>
              {message.function_call && (
                <div className="mt-2 text-xs text-gray-500">
                  Function: {message.function_call.name}
                </div>
              )}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;