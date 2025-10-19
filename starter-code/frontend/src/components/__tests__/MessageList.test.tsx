import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MessageList from '../MessageList';
import { Message } from '../../hooks/useSSEConnection';

// Mock FunctionCallRenderer to avoid complex dependencies
jest.mock('../FunctionCallRenderer', () => {
  return function MockFunctionCallRenderer({ functionCall }: any) {
    return (
      <div data-testid="function-call-renderer">
        {functionCall.name}
      </div>
    );
  };
});

describe('MessageList', () => {
  const mockOnInteraction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering Different Message Types', () => {
    it('should render user messages', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'user',
          content: 'Hello, how are you?',
          timestamp: new Date('2024-01-01T12:00:00'),
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
      // Check the parent div has the blue background class
      const messageElement = screen.getByText('Hello, how are you?');
      const messageContainer = messageElement.closest('.bg-blue-500');
      expect(messageContainer).toBeInTheDocument();
    });

    it('should render assistant messages', () => {
      const messages: Message[] = [
        {
          id: 'msg-2',
          type: 'assistant',
          content: 'I am doing great!',
          timestamp: new Date('2024-01-01T12:01:00'),
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.getByText('I am doing great!')).toBeInTheDocument();
      const messageDiv = screen.getByText('I am doing great!').closest('div');
      expect(messageDiv).toHaveClass('bg-gray-100');
    });

    it('should render error messages', () => {
      const messages: Message[] = [
        {
          id: 'msg-3',
          type: 'error',
          content: 'Something went wrong',
          timestamp: new Date('2024-01-01T12:02:00'),
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      const errorDiv = screen.getByText('Something went wrong').closest('div.border');
      expect(errorDiv).toHaveClass('bg-red-50', 'border-red-200');
    });

    it('should render function call messages', () => {
      const messages: Message[] = [
        {
          id: 'msg-4',
          type: 'function_call',
          content: 'Executing search_products',
          timestamp: new Date('2024-01-01T12:03:00'),
          function_call: {
            name: 'search_products',
            parameters: { query: 'headphones' },
            result: {
              success: true,
              data: { products: [] },
            },
          },
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.getByText('Executing search_products')).toBeInTheDocument();
      expect(screen.getByTestId('function-call-renderer')).toBeInTheDocument();
    });
  });

  describe('Message Timestamps', () => {
    it('should display timestamps for all messages', () => {
      const timestamp = new Date('2024-01-01T15:30:45');
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'user',
          content: 'Test message',
          timestamp,
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      const timeString = timestamp.toLocaleTimeString();
      expect(screen.getByText(timeString)).toBeInTheDocument();
    });
  });

  describe('Multiple Messages', () => {
    it('should render multiple messages in order', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'user',
          content: 'First message',
          timestamp: new Date('2024-01-01T12:00:00'),
        },
        {
          id: 'msg-2',
          type: 'assistant',
          content: 'Second message',
          timestamp: new Date('2024-01-01T12:01:00'),
        },
        {
          id: 'msg-3',
          type: 'user',
          content: 'Third message',
          timestamp: new Date('2024-01-01T12:02:00'),
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText('Second message')).toBeInTheDocument();
      expect(screen.getByText('Third message')).toBeInTheDocument();
    });

    it('should render empty list when no messages', () => {
      const { container } = render(
        <MessageList messages={[]} onInteraction={mockOnInteraction} />
      );

      expect(container.querySelector('.space-y-4')).toBeEmptyDOMElement();
    });
  });

  describe('Function Call Rendering', () => {
    it('should only render function call component when result is successful', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'function_call',
          content: 'Executing function',
          timestamp: new Date(),
          function_call: {
            name: 'test_function',
            parameters: {},
            result: {
              success: true,
              data: { test: 'data' },
            },
          },
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.getByTestId('function-call-renderer')).toBeInTheDocument();
    });

    it('should not render function call component when result is unsuccessful', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'function_call',
          content: 'Executing function',
          timestamp: new Date(),
          function_call: {
            name: 'test_function',
            parameters: {},
            result: {
              success: false,
              error: 'Function failed',
            },
          },
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.queryByTestId('function-call-renderer')).not.toBeInTheDocument();
    });

    it('should not render function call component when no result data', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'function_call',
          content: 'Executing function',
          timestamp: new Date(),
          function_call: {
            name: 'test_function',
            parameters: {},
            result: {
              success: true,
              data: null,
            },
          },
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      expect(screen.queryByTestId('function-call-renderer')).not.toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('should apply correct styling for user messages (right-aligned)', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'user',
          content: 'User message',
          timestamp: new Date(),
        },
      ];

      const { container } = render(
        <MessageList messages={messages} onInteraction={mockOnInteraction} />
      );

      const messageContainer = container.querySelector('.justify-end');
      expect(messageContainer).toBeInTheDocument();
    });

    it('should apply correct styling for assistant messages (left-aligned)', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'assistant',
          content: 'Assistant message',
          timestamp: new Date(),
        },
      ];

      const { container } = render(
        <MessageList messages={messages} onInteraction={mockOnInteraction} />
      );

      const messageContainer = container.querySelector('.flex.items-start');
      expect(messageContainer).toBeInTheDocument();
      expect(messageContainer?.querySelector('.bg-gray-100')).toBeInTheDocument();
    });
  });

  describe('Content Handling', () => {
    it('should preserve whitespace in message content', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'user',
          content: 'Line 1\nLine 2\n\nLine 3',
          timestamp: new Date(),
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      const messageElement = screen.getByText(/Line 1/);
      expect(messageElement).toHaveClass('whitespace-pre-wrap');
    });

    it('should handle empty message content', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'user',
          content: '',
          timestamp: new Date(),
        },
      ];

      const { container } = render(
        <MessageList messages={messages} onInteraction={mockOnInteraction} />
      );

      expect(container.querySelector('.bg-blue-500')).toBeInTheDocument();
    });
  });

  describe('Interaction Handling', () => {
    it('should pass onInteraction to FunctionCallRenderer', () => {
      const messages: Message[] = [
        {
          id: 'msg-1',
          type: 'function_call',
          content: 'Function call',
          timestamp: new Date(),
          function_call: {
            name: 'test_function',
            parameters: {},
            result: {
              success: true,
              data: {},
            },
          },
        },
      ];

      render(<MessageList messages={messages} onInteraction={mockOnInteraction} />);

      // FunctionCallRenderer should receive onInteraction prop
      expect(screen.getByTestId('function-call-renderer')).toBeInTheDocument();
    });
  });
});

