# Backend Test Suite

## Overview

This directory contains **comprehensive production backend tests** covering:
- ✅ API Endpoints (health, session, search, cart, recommendations)
- ✅ SSE Streaming (connection, messages, events, error handling)
- ✅ Product Service (search, details, recommendations)
- ✅ Context Manager (validation, session management)
- ✅ Database Models (CRUD, relationships, transactions)
- ✅ AI Agent (streaming, function calling, tool definitions)
- ✅ Rate Limiting (endpoint limits, error handling)

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_api_endpoints.py    # API endpoint tests (45 tests)
├── test_sse_streaming.py    # SSE functionality tests (22 tests)
├── test_product_service.py  # Product service tests (15 tests)
├── test_context_manager.py  # Context validation tests (18 tests)
├── test_database.py         # Database model tests (25 tests)
├── test_ai_agent.py         # AI agent tests (10 tests)
└── test_rate_limiting.py    # Rate limiting tests (2 tests)
```

## Running Tests

### Option 1: In Docker (Recommended)

```bash
# Start the backend container
docker-compose up -d backend

# Run all tests
docker-compose exec backend python -m pytest tests/ -v

# Run specific test file
docker-compose exec backend python -m pytest tests/test_product_service.py -v

# Run with coverage
docker-compose exec backend python -m pytest tests/ --cov=. --cov-report=html
```

### Option 2: Local Development

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Set environment variables
export ENVIRONMENT=test
export DATABASE_URL=sqlite+aiosqlite:///:memory:
export RATE_LIMITING_ENABLED=false
export SKIP_DB_INIT=true

# Run tests
python -m pytest tests/ -v
```

### Option 3: Quick Validation

```bash
# Run tests with test database
python -m pytest tests/ -k "test_health" -v
```

## Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| API Endpoints | 45 | All endpoints, error cases, validation |
| SSE Streaming | 22 | Connection, messages, concurrency |
| Product Service | 15 | Search, details, recommendations |
| Context Manager | 18 | Validation, session management |
| Database | 25 | Models, relationships, transactions |
| AI Agent | 10 | Streaming, function calls, tools |
| Rate Limiting | 2 | Limits, error handling |
| **TOTAL** | **137** | **Comprehensive** |

## Key Test Scenarios

### 1. API Endpoints
- Health check with system info
- Session creation and management
- Product search with filters
- Product details with context validation
- Add/remove from cart
- Recommendations

### 2. SSE Streaming
- Connection establishment
- Real-time message delivery
- Event types (connection, message, error, function_call)
- Error handling
- Multiple concurrent connections

### 3. Context Validation
- Product ID validation against search results
- Session context management
- Prevention of AI hallucination
- Context expiration

### 4. Database Operations
- CRUD operations for all models
- Relationships (products, cart items, search context)
- Transactions and rollbacks
- Concurrent updates

### 5. AI Agent
- Streaming responses
- Function call execution
- Tool definitions
- Error handling

### 6. Rate Limiting
- Per-endpoint limits
- 429 error responses
- Retry-After headers

## Test Configuration

The `conftest.py` file provides:
- Async database engine with SQLite in-memory
- Test client fixtures (sync and async)
- Sample product data
- Mock session contexts
- Mock AI responses

## Continuous Integration

For CI/CD, use:

```yaml
# .github/workflows/test.yml
- name: Run Backend Tests
  run: |
    cd starter-code/backend
    python -m pytest tests/ -v --junit-xml=test-results.xml
```

## Debugging Tests

```bash
# Run with verbose output
python -m pytest tests/ -vv

# Run with print statements
python -m pytest tests/ -s

# Run specific test
python -m pytest tests/test_api_endpoints.py::TestHealthEndpoint::test_health_check -v

# Stop on first failure
python -m pytest tests/ -x
```

## Notes

- Tests use SQLite in-memory database for speed
- Rate limiting is disabled in tests
- Database initialization is skipped (using fixtures instead)
- All tests are isolated with function-scoped fixtures
- Async tests use pytest-asyncio

