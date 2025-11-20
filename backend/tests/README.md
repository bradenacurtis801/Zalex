# Backend Testing

Simple, fast, mock-based testing for the backend.

## 🎯 **Mock-Based Testing Approach**

- **No real database** - Uses mocked PostgreSQL sessions
- **No external services** - All services are mocked
- **Fast execution** - Tests run in milliseconds
- **Complete isolation** - No external dependencies

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r tests/requirements-test.txt

# Run all tests
pytest

# Run fast mock-based tests only
pytest tests/unit/ -m mock

# Run with coverage
pytest --cov=src --cov-report=html
```

## 📁 Structure

```
tests/
├── conftest.py              # SQLite in-memory configuration
├── conftest_mock.py         # Mock-based test configuration
├── unit/                    # Mock-based unit tests
│   ├── test_auth_service_mock.py
│   ├── test_upload_service_mock.py
│   └── test_query_service_mock.py
├── integration/             # Integration tests (empty)
├── e2e/                     # End-to-end tests (empty)
├── fixtures/                # Test fixtures and mocks
│   ├── mock_services.py
│   ├── test_data.py
│   └── helpers.py
├── data/                    # Test data
└── run_tests.py            # Test runner script
```

## 🎯 Test Types

- **Unit Tests** - Mock-based, fast execution
- **Integration Tests** - Real database, API testing
- **E2E Tests** - Full application testing

## 📖 Documentation

See `README_MOCK.md` for detailed documentation on mock-based testing.

## 🛠️ Commands

```bash
# Run specific test types
python tests/run_tests.py unit
python tests/run_tests.py quick
python tests/run_tests.py coverage

# Run specific tests
pytest tests/unit/test_auth_service_mock.py
pytest tests/unit/ -m mock
```
