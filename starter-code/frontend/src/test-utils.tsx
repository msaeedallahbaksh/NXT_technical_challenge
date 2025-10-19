import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { AppStateProvider } from './context/AppStateContext';

/**
 * Custom render function that wraps components with necessary providers
 */
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <AppStateProvider>
      {children}
    </AppStateProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

/**
 * Helper to create mock messages for testing
 */
export const createMockMessage = (overrides?: Partial<any>) => ({
  id: 'test-msg-1',
  type: 'user',
  content: 'Test message',
  timestamp: new Date(),
  ...overrides,
});

/**
 * Helper to create mock function calls for testing
 */
export const createMockFunctionCall = (
  name: string,
  parameters?: any,
  result?: any
) => ({
  name,
  parameters: parameters || {},
  result: result || { success: true, data: {} },
});

/**
 * Helper to wait for async updates
 */
export const waitFor = (callback: () => void, timeout = 1000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      try {
        callback();
        clearInterval(interval);
        resolve(true);
      } catch (error) {
        if (Date.now() - startTime > timeout) {
          clearInterval(interval);
          reject(error);
        }
      }
    }, 50);
  });
};

