## Test Structure

```
src/
├── setupTests.ts                          # Global test setup and mocks
├── test-utils.tsx                         # Custom render helpers and utilities
├── hooks/
│   └── __tests__/
│       └── useSSEConnection.test.ts      # SSE connection hook tests (40+ test cases)
└── components/
    └── __tests__/
        ├── MessageList.test.tsx          # Message rendering tests (25+ test cases)
        ├── FunctionCallRenderer.test.tsx # Dynamic component rendering tests (20+ test cases)
        └── ChatInterface.test.tsx        # Integration tests (25+ test cases)
```

## Running Tests

### Run All Tests
```bash
cd starter-code/frontend
npm test
```

### Run Tests in Watch Mode
```bash
npm test -- --watch
```

### Run Tests with Coverage
```bash
npm test -- --coverage
```

### Run Specific Test File
```bash
npm test -- useSSEConnection.test.ts
```

### Run Tests Matching Pattern
```bash
npm test -- --testNamePattern="should send message"
```

## Test Coverage

### 1. useSSEConnection Hook Tests (`useSSEConnection.test.ts`)

**Connection Management (6 tests)**
- ✅ Initialize with disconnected status
- ✅ Connect to SSE endpoint on mount
- ✅ Use correct SSE URL
- ✅ Handle connection errors
- ✅ Attempt reconnection on connection loss
- ✅ Cleanup connection on unmount

**Message Handling (5 tests)**
- ✅ Send a message successfully
- ✅ Add user message to messages array
- ✅ Handle message send errors
- ✅ Send context with message
- ✅ Clear messages

**Function Call Handling (3 tests)**
- ✅ Add function call message
- ✅ Update existing message
- ✅ Call onFunctionCall callback

**Typing Indicator (1 test)**
- ✅ Set isTyping when receiving text

**Callbacks (2 tests)**
- ✅ Call onMessage callback when message is added
- ✅ Call onError callback on errors

**Reconnection Logic (3 tests)**
- ✅ Stop reconnecting after max attempts
- ✅ Use exponential backoff for reconnection
- ✅ Reset reconnect attempts on successful connection

**Manual Reconnection (2 tests)**
- ✅ Provide manual reconnect function
- ✅ Reconnect when manual reconnect is called

### 2. MessageList Component Tests (`MessageList.test.tsx`)

**Rendering Different Message Types (4 tests)**
- ✅ Render user messages
- ✅ Render assistant messages
- ✅ Render error messages
- ✅ Render function call messages

**Message Timestamps (1 test)**
- ✅ Display timestamps for all messages

**Multiple Messages (2 tests)**
- ✅ Render multiple messages in order
- ✅ Render empty list when no messages

**Function Call Rendering (3 tests)**
- ✅ Only render function call component when result is successful
- ✅ Not render function call component when result is unsuccessful
- ✅ Not render function call component when no result data

**Styling and Layout (2 tests)**
- ✅ Apply correct styling for user messages (right-aligned)
- ✅ Apply correct styling for assistant messages (left-aligned)

**Content Handling (2 tests)**
- ✅ Preserve whitespace in message content
- ✅ Handle empty message content

**Interaction Handling (1 test)**
- ✅ Pass onInteraction to FunctionCallRenderer

### 3. FunctionCallRenderer Component Tests (`FunctionCallRenderer.test.tsx`)

**Component Mapping (4 tests)**
- ✅ Render SearchResults for search_products
- ✅ Render ProductDetailView for show_product_details
- ✅ Render CartNotification for add_to_cart
- ✅ Render RecommendationGrid for get_recommendations

**Unknown Function Handling (1 test)**
- ✅ Render unknown function message for unmapped functions

**Add to Cart Special Handling (3 tests)**
- ✅ Show waiting message when cart_item is missing
- ✅ Show waiting message when cart_summary is missing
- ✅ Render CartNotification when both exist

**Props Merging (3 tests)**
- ✅ Merge parameters and result data into component props
- ✅ Handle missing result data gracefully
- ✅ Handle missing result entirely

**Interaction Handling (2 tests)**
- ✅ Wrap onInteraction with function context
- ✅ Handle onInteraction being undefined

**Error Handling (2 tests)**
- ✅ Handle component rendering errors gracefully
- ✅ Render when parameters are empty

### 4. ChatInterface Integration Tests (`ChatInterface.test.tsx`)

**Component Rendering (3 tests)**
- ✅ Render all main components
- ✅ Show connection status
- ✅ Create session on mount if none exists

**Message Sending (3 tests)**
- ✅ Send message when user submits
- ✅ Clear input after sending message
- ✅ Disable input when disconnected

**Message Display (2 tests)**
- ✅ Display messages from SSE hook
- ✅ Auto-scroll to new messages

**Function Call Handling (4 tests)**
- ✅ Execute function calls
- ✅ Handle successful function call
- ✅ Handle failed function call
- ✅ Update message with function result

**Error Handling (2 tests)**
- ✅ Display error state when connection errors
- ✅ Provide reconnect functionality

**Connection State Management (3 tests)**
- ✅ Handle connecting state
- ✅ Handle connected state
- ✅ Handle disconnected state

## Test Utilities

### setupTests.ts
- Mock EventSource for SSE testing
- Mock fetch API
- Global test configuration

### test-utils.tsx
- Custom render with AppStateProvider
- Mock message creators
- Mock function call creators
- Wait utilities for async operations

## Mocking Strategy

### External Dependencies
- **EventSource**: Custom mock implementation for SSE testing
- **fetch**: Jest mock for API calls
- **Child Components**: Mocked in integration tests to isolate behavior

### Test Isolation
- Each test file uses `beforeEach` to reset mocks
- Independent test cases don't share state
- Mock implementations are scoped to test suites

## Best Practices Followed

1. **Comprehensive Coverage**: Tests cover happy paths, error cases, and edge cases
2. **Clear Test Names**: Descriptive test names following "should" convention
3. **Proper Isolation**: Each test is independent and can run in any order
4. **Real User Interactions**: Using `@testing-library/user-event` for realistic interactions
5. **Async Handling**: Proper use of `waitFor` for async operations
6. **Mock Cleanup**: All mocks are cleared between tests
7. **Type Safety**: TypeScript throughout all test files

## Coverage Goals

Target coverage for production code:
- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
```bash
# CI test command
npm test -- --ci --coverage --maxWorkers=2
```

## Debugging Tests

### Run Single Test in Debug Mode
```bash
node --inspect-brk node_modules/.bin/react-scripts test --runInBand --no-cache
```

### View Test Output with Verbose Logging
```bash
npm test -- --verbose
```

### Update Snapshots (if using snapshot tests)
```bash
npm test -- -u
```

## Common Issues and Solutions

### Issue: EventSource not defined
**Solution**: Make sure `setupTests.ts` is properly configured with the EventSource mock.

### Issue: Tests timeout
**Solution**: Increase timeout for async operations or check for unresolved promises.

### Issue: Mock not working
**Solution**: Ensure mocks are defined before importing the component being tested.

## Future Test Additions

Consider adding:
- E2E tests with Cypress or Playwright
- Visual regression tests
- Performance tests
- Accessibility tests (a11y)
- Storybook interaction tests

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

