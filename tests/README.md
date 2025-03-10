# SociSphere Tests

This directory contains tests for the SociSphere platform, including backend API tests and frontend client loading tests.

## Test Types

- **API Tests**: Tests for the REST API endpoints
- **Model Tests**: Tests for Django models and their methods
- **Client Tests**: Tests for client-side loading and interaction
  - Basic client loading tests
  - JavaScript functionality tests using Selenium
  - User journey integration tests
  - API mocking tests

## Requirements

Install test dependencies:

```bash
pip install -r tests/requirements-test.txt
```

For Selenium tests, you'll need Chrome and ChromeDriver installed. You can install ChromeDriver using:

```bash
# For macOS with Homebrew
brew install --cask chromedriver

# For Ubuntu/Debian
apt-get install chromium-chromedriver
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run specific test modules

```bash
# Run only client loading tests
pytest tests/client/test_client_loading.py

# Run JavaScript-specific tests
pytest tests/client/test_client_js.py

# Run API mocking tests
pytest tests/client/test_api_mocking.py

# Run user journey tests
pytest tests/client/test_user_journey.py
```

### Run with coverage report

```bash
pytest --cov=apps --cov=socisphere --cov-report=html
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. For headless browser testing in CI environments, Selenium tests use the `--headless` Chrome option.

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **UI Tests**: Test the user interface using Selenium
- **End-to-End Tests**: Test complete user journeys through the application

## Writing New Tests

When adding new features:

1. Add unit tests for new models, views, and services
2. Update integration tests for component interactions
3. Add Selenium tests for UI components
4. Consider updating user journey tests for major features 