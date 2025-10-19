/**
 * Custom hook for managing Server-Sent Events (SSE) connection
 * 
 * This hook provides:
 * - Real-time SSE connection management
 * - Message parsing and state management
 * - Auto-reconnection with exponential backoff
 * - Function call event handling
 * - Error handling and recovery
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'function_call' | 'error';
  content: string;
  timestamp: Date;
  function_call?: {
    name: string;
    parameters: Record<string, any>;
    result?: any;
  };
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface SSEConnectionOptions {
  sessionId: string;
  onMessage?: (message: Message) => void;
  onFunctionCall?: (functionCall: any) => void;
  onError?: (error: string) => void;
  maxReconnectAttempts?: number;
  baseReconnectDelay?: number;
}

export interface SSEConnectionHook {
  messages: Message[];
  connectionStatus: ConnectionStatus;
  sendMessage: (message: string, context?: Record<string, any>) => Promise<void>;
  clearMessages: () => void;
  reconnect: () => void;
  error: string | null;
  isTyping: boolean;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  addFunctionCallMessage: (functionCall: { name: string; parameters: any; result?: any }) => string;
}

export const useSSEConnection = (options: SSEConnectionOptions): SSEConnectionHook => {
  const {
    sessionId,
    onMessage,
    onFunctionCall,
    onError,
    maxReconnectAttempts = 5,
    baseReconnectDelay = 1000,
  } = options;

  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  
  // Refs for managing connection
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const toolCallMapRef = useRef<Map<string, string>>(new Map()); // Maps tool_call_id -> message_id

  // Base API URL
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  /**
   * Add a message to the messages array
   */
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
    onMessage?.(message);
  }, [onMessage]);

  /**
   * Connect to SSE stream
   */
  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setConnectionStatus('connecting');
    setError(null);

    try {
      const eventSource = new EventSource(`${API_URL}/api/stream/${sessionId}`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setConnectionStatus('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different event types
          handleSSEEvent(data, event.type || 'message');
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
        }
      };

      // Handle specific event types
      eventSource.addEventListener('text_chunk', (event) => {
        const data = JSON.parse(event.data);
        handleTextChunk(data);
      });

      eventSource.addEventListener('function_call', (event) => {
        const data = JSON.parse(event.data);
        handleFunctionCall(data);
      });

      eventSource.addEventListener('function_result', (event) => {
        const data = JSON.parse(event.data);
        handleFunctionResult(data);
      });

      eventSource.addEventListener('completion', (event) => {
        const data = JSON.parse(event.data);
        handleCompletion(data);
      });

      eventSource.addEventListener('error', (event: any) => {
        try {
          const data = JSON.parse(event.data);
          handleErrorEvent(data);
        } catch (err) {
          console.error('Failed to parse error event:', err);
        }
      });

      eventSource.onerror = (event) => {
        console.error('SSE error:', event);
        setConnectionStatus('error');
        
        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          scheduleReconnect();
        } else {
          setError('Max reconnection attempts reached');
          onError?.('Max reconnection attempts reached');
        }
      };

    } catch (err) {
      console.error('Failed to create SSE connection:', err);
      setConnectionStatus('error');
      setError('Failed to establish connection');
      onError?.('Failed to establish connection');
    }
  }, [sessionId, API_URL, maxReconnectAttempts, onError]);

  /**
   * Handle generic SSE events
   */
  const handleSSEEvent = (data: any, eventType: string) => {
    switch (eventType) {
      case 'connection':
        // Connection established
        break;
      default:
        // Unknown event type - silently ignore
        break;
    }
  };

  /**
   * Handle text chunk streaming
   */
  const handleTextChunk = (data: any) => {
    const { content, partial } = data;
    
    if (partial) {
      // Update the last assistant message or create a new one
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        
        if (lastMessage && lastMessage.type === 'assistant') {
          // Append to existing message
          return prev.map((msg, index) => 
            index === prev.length - 1 
              ? { ...msg, content: msg.content + content }
              : msg
          );
        } else {
          // Create new assistant message
          return [...prev, {
            id: `msg_${Date.now()}`,
            type: 'assistant',
            content,
            timestamp: new Date()
          }];
        }
      });
    } else {
      // Complete message
      addMessage({
        id: `msg_${Date.now()}`,
        type: 'assistant',
        content,
        timestamp: new Date()
      });
    }

    setIsTyping(true);
  };

  /**
   * Handle function call events
   */
  const handleFunctionCall = (data: any) => {
    const { function: functionName, parameters, result, tool_call_id } = data;
    
    // Store the message ID keyed by tool_call_id for result updates
    const messageId = `func_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    if (tool_call_id) {
      toolCallMapRef.current.set(tool_call_id, messageId);
    }
    
    const message: Message = {
      id: messageId,
      type: 'function_call',
      content: `Executing ${functionName}`,
      timestamp: new Date(),
      function_call: {
        name: functionName,
        parameters,
        result
      }
    };

    addMessage(message);
  };
  
  /**
   * Handle function result events from backend
   */
  const handleFunctionResult = (data: any) => {
    const { function: functionName, result, tool_call_id } = data;
    
    // Find the message to update using tool_call_id
    const messageId = tool_call_id ? toolCallMapRef.current.get(tool_call_id) : null;
    
    if (messageId) {
      // Update the existing function call message with results
      setMessages(prev => prev.map(msg => {
        if (msg.id === messageId && msg.function_call) {
          return {
            ...msg,
            content: result.success 
              ? `Completed ${functionName}` 
              : `Error in ${functionName}: ${result.error}`,
            function_call: {
              ...msg.function_call,
              result
            }
          };
        }
        return msg;
      }));
      
      // Clean up the mapping
      if (tool_call_id) {
        toolCallMapRef.current.delete(tool_call_id);
      }
    } else {
      console.warn('No message found for tool_call_id:', tool_call_id);
    }
  };
  
  /**
   * Update a message with new data (e.g., function call results)
   */
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
  }, []);

  /**
   * Add a new function call message (for user-initiated function calls)
   */
  const addFunctionCallMessage = useCallback((functionCall: { name: string; parameters: any; result?: any }): string => {
    const messageId = `func_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const message: Message = {
      id: messageId,
      type: 'function_call',
      content: `Executing ${functionCall.name}`,
      timestamp: new Date(),
      function_call: {
        name: functionCall.name,
        parameters: functionCall.parameters,
        result: functionCall.result
      }
    };
    addMessage(message);
    return messageId;
  }, [addMessage]);

  /**
   * Handle completion events
   */
  const handleCompletion = (data: any) => {
    setIsTyping(false);
  };

  /**
   * Handle error events
   */
  const handleErrorEvent = (data: any) => {
    const errorMessage: Message = {
      id: `error_${Date.now()}`,
      type: 'error',
      content: data.error || 'An error occurred',
      timestamp: new Date()
    };

    addMessage(errorMessage);
    setError(data.error);
    onError?.(data.error);
  };

  /**
   * Schedule reconnection with exponential backoff
   */
  const scheduleReconnect = () => {
    const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttemptsRef.current++;
      connect();
    }, delay);
  };

  /**
   * Send a message to the backend
   */
  const sendMessage = async (message: string, context?: Record<string, any>) => {
    if (!abortControllerRef.current) {
      abortControllerRef.current = new AbortController();
    }

    try {
      // Add user message immediately
      addMessage({
        id: `user_${Date.now()}`,
        type: 'user',
        content: message,
        timestamp: new Date()
      });

      // Send message to backend
      const response = await fetch(`${API_URL}/api/chat/${sessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          context: context || {}
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await response.json();

    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Failed to send message:', err);
        setError('Failed to send message');
        onError?.('Failed to send message');
      }
    }
  };

  /**
   * Clear all messages
   */
  const clearMessages = () => {
    setMessages([]);
  };

  /**
   * Manually trigger reconnection
   */
  const reconnect = () => {
    reconnectAttemptsRef.current = 0;
    connect();
  };

  /**
   * Disconnect and cleanup
   */
  const disconnect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setConnectionStatus('disconnected');
  };

  // Auto-connect on mount (only once)
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]); // Only reconnect if sessionId changes

  return {
    messages,
    connectionStatus,
    sendMessage,
    clearMessages,
    reconnect,
    error,
    isTyping,
    updateMessage,
    addFunctionCallMessage
  };
};