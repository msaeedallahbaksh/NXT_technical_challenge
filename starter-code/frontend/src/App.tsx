import React from 'react';
import ChatInterface from './components/ChatInterface';
import CartSidebar from './components/CartSidebar';
import { AppStateProvider, useAppState } from './context/AppStateContext';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

/**
 * Main App component for the AI Product Discovery Assistant.
 * 
 * Features:
 * - Real-time chat interface with AI assistant
 * - Server-Sent Events (SSE) for streaming responses
 * - Dynamic component rendering based on AI function calls
 * - Cart sidebar with live updates
 * - Context management and error boundaries
 */

const AppContent: React.FC = () => {
  const { sessionId } = useAppState();

  return (
    <div className="App min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-bold">AI</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Product Discovery Assistant
              </h1>
              <p className="text-sm text-gray-500">
                Your AI-powered shopping companion
              </p>
            </div>
          </div>
        </div>
      </header>
      
      <main className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Chat Interface - Takes 2/3 of the space */}
          <div className="lg:col-span-2">
            <ChatInterface />
          </div>
          
          {/* Cart Sidebar - Takes 1/3 of the space */}
          <div className="lg:col-span-1">
            <CartSidebar sessionId={sessionId || ''} />
          </div>
        </div>
      </main>
      
      <footer className="text-center py-4 text-sm text-gray-500">
        <p>NXT Humans Technical Challenge - AI Product Discovery Assistant</p>
      </footer>
    </div>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <AppStateProvider>
        <AppContent />
      </AppStateProvider>
    </ErrorBoundary>
  );
}

export default App;