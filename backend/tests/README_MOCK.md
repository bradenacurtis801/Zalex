# ScanPro Backend Testing - Mock-Based Approach

This document describes the **mock-based testing approach** for the ScanPro backend, which focuses on fast, isolated unit tests without external dependencies.

## 🎯 **Why Mock-Based Testing?**

### **Advantages:**
- ⚡ **Fast execution** - No database I/O or external service calls
- 🔒 **Complete isolation** - Tests don't affect each other
- 🚀 **Easy CI/CD** - No external dependencies to manage
- 🛠️ **Simple setup** - Just run `pytest` and go
- 🎯 **Focused testing** - Tests business logic, not infrastructure

### **When to Use:**
- **Unit tests** (70% of your test suite)
- **Service layer testing** (business logic)
- **Fast feedback during development**
- **CI/CD pipelines**

## 📁 **Test Structure**

```
backend/tests/
├── conftest_mock.py          # Mock-based test configuration
├── conftest.py               # SQLite in-memory configuration
├── unit/                     # Unit tests with mocked dependencies
│   ├── test_auth_service_mock.py
│   ├── test_upload_service_mock.py
│   └── test_query_service_mock.py
├── integration/              # Integration tests (real database)
├── e2e/                      # End-to-end tests (full stack)
└── fixtures/                 # Test fixtures and mocks
    ├── mock_services.py
    ├── test_data.py
    └── helpers.py
```

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
cd backend
pip install -r tests/requirements-test.txt
```

### **2. Run Mock-Based Tests**
```bash
# Run all mock-based unit tests
pytest tests/unit/ -m mock

# Run specific test file
pytest tests/unit/test_auth_service_mock.py

# Run with coverage
pytest tests/unit/ -m mock --cov=src --cov-report=html

# Run fast tests only
pytest tests/unit/ -m "mock and fast"
```

### **3. Run All Tests**
```bash
# Run all tests (unit + integration + e2e)
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_auth_service_mock.py::TestAuthServiceMocked::test_create_user_success
```

## 🧪 **Test Categories**

### **Unit Tests (Mock-Based)**
- **Location:** `tests/unit/`
- **Markers:** `@pytest.mark.mock`, `@pytest.mark.fast`
- **Database:** SQLite in-memory or mocked
- **External Services:** Mocked
- **Speed:** Very fast (< 1ms per test)

### **Integration Tests**
- **Location:** `tests/integration/`
- **Markers:** `@pytest.mark.integration`
- **Database:** SQLite in-memory
- **External Services:** Mocked
- **Speed:** Fast (< 10ms per test)

### **End-to-End Tests**
- **Location:** `tests/e2e/`
- **Markers:** `@pytest.mark.e2e`
- **Database:** Real PostgreSQL (optional)
- **External Services:** Real or mocked
- **Speed:** Slower (< 100ms per test)

## 🔧 **Mock Configuration**

### **Database Mocking**
```python
@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests."""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.get = Mock()
    mock_session.exec = Mock()
    return mock_session
```

### **Service Mocking**
```python
@pytest.fixture
def mock_auth_service(mock_db_session):
    """Mock auth service for testing."""
    from src.services.auth_service import AuthService
    return Mock(spec=AuthService)
```

### **External Service Mocking**
```python
@pytest.fixture
def mock_ocr_engine():
    """Mock OCR engine for testing."""
    from tests.fixtures.mock_services import MockOCREngine
    return MockOCREngine()
```

## 📝 **Writing Mock-Based Tests**

### **Example: AuthService Test**
```python
@pytest.mark.mock
@pytest.mark.fast
def test_create_user_success(self, mock_db_session):
    """Test successful user creation with mocked database."""
    # Arrange
    auth_service = AuthService(mock_db_session)
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="password123",
        user_role=UserRole.USER
    )
    
    # Mock database responses
    mock_db_session.exec.return_value.first.return_value = None  # No existing user
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    
    # Act
    with patch('src.services.auth_service.pwd_context') as mock_pwd:
        mock_pwd.hash.return_value = "hashed_password"
        result = auth_service.create_user(user_data)
    
    # Assert
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
```

## 🎯 **Test Markers**

### **Available Markers:**
- `@pytest.mark.mock` - Mock-based unit tests
- `@pytest.mark.fast` - Fast-running tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests

### **Running Tests by Marker:**
```bash
# Run only mock-based tests
pytest -m mock

# Run only fast tests
pytest -m fast

# Run unit tests (mock + integration)
pytest -m unit

# Run all tests except e2e
pytest -m "not e2e"
```

## 📊 **Test Coverage**

### **Coverage Targets:**
- **Unit Tests:** 90%+ coverage
- **Integration Tests:** 80%+ coverage
- **E2E Tests:** 70%+ coverage
- **Overall:** 85%+ coverage

### **Coverage Commands:**
```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Coverage with specific tests
pytest tests/unit/ -m mock --cov=src --cov-report=term-missing

# Coverage threshold
pytest --cov=src --cov-fail-under=85
```

## 🚨 **Common Patterns**

### **1. Mocking Database Queries**
```python
# Mock successful query
mock_db_session.exec.return_value.all.return_value = [mock_user]

# Mock empty query
mock_db_session.exec.return_value.all.return_value = []

# Mock single result
mock_db_session.exec.return_value.first.return_value = mock_user
```

### **2. Mocking External Services**
```python
# Mock OCR engine
with patch('src.utils.document_processor.ocr_engine') as mock_ocr:
    mock_ocr.extract_text.return_value = "extracted text"
    result = process_document(file_content)
```

### **3. Mocking File Operations**
```python
# Mock file reading
with patch('builtins.open', create=True) as mock_open:
    mock_open.return_value.__enter__.return_value.read.return_value = b"file content"
    result = read_file("path/to/file")
```

### **4. Mocking HTTP Requests**
```python
# Mock HTTP client
with patch('httpx.AsyncClient') as mock_client:
    mock_client.return_value.post.return_value = Mock(status_code=200, json=lambda: {"result": "success"})
    result = make_api_call()
```

## 🔍 **Debugging Tests**

### **Verbose Output:**
```bash
# Show test names and results
pytest -v

# Show print statements
pytest -s

# Show local variables on failure
pytest --tb=long
```

### **Debugging Specific Tests:**
```bash
# Run single test with debugging
pytest tests/unit/test_auth_service_mock.py::TestAuthServiceMocked::test_create_user_success -v -s

# Run with pdb on failure
pytest --pdb

# Run with pdb on first failure
pytest -x --pdb
```

## 📈 **Performance Testing**

### **Benchmark Tests:**
```python
@pytest.mark.benchmark
def test_auth_service_performance(benchmark, mock_db_session):
    """Benchmark auth service performance."""
    auth_service = AuthService(mock_db_session)
    user_data = UserCreate(...)
    
    result = benchmark(auth_service.create_user, user_data)
    assert result is not None
```

### **Memory Profiling:**
```python
@pytest.mark.profile
def test_memory_usage(mock_db_session):
    """Test memory usage of auth service."""
    from memory_profiler import profile
    
    @profile
    def create_multiple_users():
        auth_service = AuthService(mock_db_session)
        for i in range(100):
            user_data = UserCreate(...)
            auth_service.create_user(user_data)
    
    create_multiple_users()
```

## 🎯 **Best Practices**

### **1. Test Naming**
- Use descriptive test names: `test_create_user_success`
- Include the scenario: `test_create_user_duplicate_username`
- Use consistent naming: `test_<method>_<scenario>`

### **2. Test Structure**
- **Arrange:** Set up test data and mocks
- **Act:** Execute the code under test
- **Assert:** Verify the results

### **3. Mock Management**
- Use `spec` parameter for better error detection
- Verify mock calls with `assert_called_once()`
- Reset mocks between tests with `autouse=True`

### **4. Test Data**
- Use factories for consistent test data
- Keep test data minimal and focused
- Use meaningful test values

### **5. Assertions**
- Use specific assertions: `assert result.username == "testuser"`
- Test both positive and negative cases
- Verify side effects: `mock_db_session.add.assert_called_once()`

## 🚀 **CI/CD Integration**

### **GitHub Actions Example:**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/tests/requirements-test.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/unit/ -m mock --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📚 **Additional Resources**

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)

## 🤝 **Contributing**

When adding new tests:

1. **Follow the naming convention:** `test_<method>_<scenario>`
2. **Use appropriate markers:** `@pytest.mark.mock`, `@pytest.mark.fast`
3. **Mock external dependencies:** Database, services, file I/O
4. **Test both success and failure cases**
5. **Verify mock interactions:** `assert_called_once()`, `assert_called_with()`
6. **Keep tests focused:** One assertion per test when possible
7. **Use descriptive docstrings:** Explain what the test verifies

## 🎉 **Summary**

The mock-based testing approach provides:

- ⚡ **Fast execution** - Tests run in milliseconds
- 🔒 **Reliable isolation** - No external dependencies
- 🚀 **Easy setup** - Just run `pytest`
- 🎯 **Focused testing** - Business logic only
- 🛠️ **Simple maintenance** - No database setup required

This approach is perfect for **unit testing** and **rapid development cycles**. For more comprehensive testing, combine with integration and E2E tests as needed.
