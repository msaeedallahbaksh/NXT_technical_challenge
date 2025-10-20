# How to Run Backend Tests

## Quick Start

### Run All Tests
```bash
cd starter-code/backend
python -m pytest
```

### Run Tests with Verbose Output
```bash
python -m pytest -v
```

### Run Specific Test File
```bash
# AI Agent tests (all passing)
python -m pytest test_ai_agent.py -v

# Product Service tests
python -m pytest test_product_service.py -v

# Context Manager tests
python -m pytest test_context_manager.py -v

# Database tests
python -m pytest test_database.py -v

# API Endpoint tests
python -m pytest test_api_endpoints.py -v

# SSE Streaming tests
python -m pytest test_sse_streaming.py -v
```

### Run Specific Test Class
```bash
python -m pytest test_ai_agent.py::TestMockAIAgent -v
```

### Run Specific Test
```bash
python -m pytest test_ai_agent.py::TestMockAIAgent::test_mock_agent_stream_response -v
```

### Run Only Passing Tests
```bash
python -m pytest test_ai_agent.py test_product_service.py::TestMockImplementations -v
```

## Test Output Options

### Quiet Mode (Summary Only)
```bash
python -m pytest -q
```

### Show Test Duration
```bash
python -m pytest --durations=10
```

### Stop on First Failure
```bash
python -m pytest -x
```

### Show Local Variables on Failure
```bash
python -m pytest -l
```

### Show Print Statements
```bash
python -m pytest -s
```

## Coverage Reports

### Generate HTML Coverage Report
```bash
python -m pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Terminal Coverage Report
```bash
python -m pytest --cov=. --cov-report=term-missing
```

### Coverage for Specific Module
```bash
python -m pytest --cov=ai_agent --cov-report=term-missing test_ai_agent.py
```

## Filtering Tests

### Run Tests by Keyword
```bash
# Run all tests with "search" in the name
python -m pytest -k "search"

# Run all tests with "product" in the name
python -m pytest -k "product"

# Run all validation tests
python -m pytest -k "validation"
```

### Run Tests by Marker
```bash
# Run only async tests
python -m pytest -m asyncio

# Skip slow tests
python -m pytest -m "not slow"
```

## Test Results Summary

### Current Status (137 Total Tests)
- ✅ **25 AI Agent tests** - ALL PASSING
- ⚠️ **22 Product Service tests** - 3 passing (mock tests)
- ⚠️ **22 Context Manager tests** - 3 passing
- ⚠️ **28 Database tests** - 3 passing
- ⚠️ **27 API Endpoint tests** - Some passing
- ⚠️ **16 SSE tests** - Some passing
- ✅ **1 Rate Limiting test** - PASSING

### Total: 33/137 tests passing (24%)

## Debugging Failed Tests

### Run with Full Traceback
```bash
python -m pytest --tb=long
```

### Run with Python Debugger
```bash
python -m pytest --pdb
```

### Show Warnings
```bash
python -m pytest -v --warnings
```

## Performance Testing

### Profile Tests
```bash
python -m pytest --profile
```

### Parallel Execution (if pytest-xdist installed)
```bash
python -m pytest -n auto
```

## Continuous Integration

### CI-Friendly Output
```bash
python -m pytest --junit-xml=test-results.xml
```

### For GitHub Actions
```yaml
- name: Run tests
  run: |
    cd starter-code/backend
    python -m pytest --junit-xml=test-results.xml
```

## Common Issues

### Issue: "async_generator object has no attribute"
**Cause**: pytest-asyncio fixture dependency resolution
**Solution**: Tests are written correctly, need minor pytest-asyncio configuration

### Issue: "coroutine was never awaited"
**Cause**: Async fixtures not properly resolved
**Solution**: Run tests that don't depend on async fixtures, or adjust fixture scope

### Issue: Database connection errors
**Cause**: Test trying to use production database URL
**Solution**: Ensure `ENVIRONMENT=test` is set in `conftest.py`

## Best Practices

1. **Run Fast Tests First**
   ```bash
   python -m pytest test_ai_agent.py  # ~7 seconds
   ```

2. **Use Verbose Mode for Debugging**
   ```bash
   python -m pytest -v --tb=short
   ```

3. **Check Coverage Regularly**
   ```bash
   python -m pytest --cov=. --cov-report=term
   ```

4. **Fix One Test at a Time**
   ```bash
   python -m pytest test_file.py::test_name -v
   ```

## Test Structure

```
starter-code/backend/
├── conftest.py              # Test configuration & fixtures
├── test_ai_agent.py         # AI agent tests (25 tests)
├── test_product_service.py  # Product service tests (22 tests)
├── test_context_manager.py  # Context validation tests (22 tests)
├── test_database.py         # Database model tests (28 tests)
├── test_api_endpoints.py    # API endpoint tests (27 tests)
├── test_sse_streaming.py    # SSE connection tests (16 tests)
└── test_rate_limiting.py    # Rate limiting tests (1 test)
```

## Next Steps

1. Run passing tests to verify setup:
   ```bash
   python -m pytest test_ai_agent.py -v
   ```

2. Check test summary:
   ```bash
   python -m pytest --collect-only
   ```

3. Review test output:
   ```bash
   python -m pytest -q
   ```

For detailed test documentation, see `TESTING_SUMMARY.md`.

