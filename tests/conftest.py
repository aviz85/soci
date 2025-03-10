import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client for testing."""
    return APIClient()


@pytest.fixture
def user_data():
    """Return user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def create_user(user_data):
    """Create and return a test user."""
    return User.objects.create_user(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"]
    )


@pytest.fixture
def authenticated_client(api_client, create_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=create_user)
    return api_client


@pytest.fixture
def selenium(request):
    """
    Provide a selenium webdriver instance for browser testing.
    Defaults to Chrome, but will use Firefox if Chrome is not available.
    """
    browser_name = os.environ.get('SELENIUM_BROWSER', 'chrome').lower()
    
    if browser_name == 'chrome':
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options
            )
        except Exception as e:
            print(f"Chrome driver initialization failed: {e}. Falling back to Firefox.")
            browser_name = 'firefox'
    
    if browser_name == 'firefox':
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=options
        )
    
    driver.implicitly_wait(10)
    driver.set_window_size(1920, 1080)
    
    # Yield the driver to the test function
    yield driver
    
    # Quit the driver after the test is completed
    driver.quit() 