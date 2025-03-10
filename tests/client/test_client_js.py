import time
import json
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class ClientJavaScriptTests(StaticLiveServerTestCase):
    """Tests for client-side JavaScript functionality using Selenium"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize the WebDriver
        cls.selenium = webdriver.Chrome(options=chrome_options)
        cls.selenium.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Generate auth token
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
    
    def login_via_browser(self):
        """Log in using the browser interface"""
        self.selenium.get(f'{self.live_server_url}/login/')
        
        # Enter login credentials
        username_input = self.selenium.find_element(By.NAME, 'username')
        password_input = self.selenium.find_element(By.NAME, 'password')
        submit_button = self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        
        username_input.send_keys('testuser')
        password_input.send_keys('testpass123')
        submit_button.click()
        
        # Wait for redirect to homepage
        WebDriverWait(self.selenium, 10).until(
            EC.url_to_be(f'{self.live_server_url}/')
        )
    
    def login_via_local_storage(self):
        """Set JWT token directly in localStorage to bypass login form"""
        self.selenium.get(f'{self.live_server_url}/')
        
        # Set tokens in localStorage
        token_script = f"""
        localStorage.setItem('access_token', '{self.access_token}');
        localStorage.setItem('refresh_token', '{str(self.refresh)}');
        """
        self.selenium.execute_script(token_script)
        
        # Also set test user data in sessionStorage
        user_data = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'profile_image': None
        }
        user_script = f"""
        sessionStorage.setItem('current_user', '{json.dumps(user_data)}');
        """
        self.selenium.execute_script(user_script)
        
        # Reload the page to apply the token
        self.selenium.get(f'{self.live_server_url}/')
    
    def test_user_profile_updates(self):
        """Test that the user profile section updates with correct user data"""
        self.login_via_local_storage()
        
        # Wait for the profile section to load with user data
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.ID, 'user-name'), 'Test User')
        )
        
        # Verify username display
        username_element = self.selenium.find_element(By.ID, 'user-username')
        self.assertEqual(username_element.text, '@testuser')
    
    def test_feed_tabs_switch(self):
        """Test that feed tabs switch correctly"""
        self.login_via_local_storage()
        
        # Wait for page to load completely
        time.sleep(2)
        
        # Get all feed tabs
        feed_tabs = self.selenium.find_elements(By.CSS_SELECTOR, '.feed-tab')
        
        # Initially, the "For You" tab should be active
        self.assertTrue('active' in feed_tabs[0].get_attribute('class'))
        
        # Click on the "Following" tab
        feed_tabs[1].click()
        time.sleep(1)
        
        # Verify "Following" tab is now active
        feed_tabs = self.selenium.find_elements(By.CSS_SELECTOR, '.feed-tab')
        self.assertTrue('active' in feed_tabs[1].get_attribute('class'))
        self.assertFalse('active' in feed_tabs[0].get_attribute('class'))
    
    def test_post_creation_form_visibility(self):
        """Test that the post creation form toggles visibility"""
        self.login_via_local_storage()
        
        # Wait for page to load completely
        time.sleep(2)
        
        # Check that post options are initially hidden
        post_options = self.selenium.find_element(By.ID, 'create-post-options')
        self.assertTrue('hidden' in post_options.get_attribute('class'))
        
        # Click the visibility button to show options
        visibility_btn = self.selenium.find_element(By.ID, 'visibility-btn')
        visibility_btn.click()
        
        # Verify options are now visible
        post_options = self.selenium.find_element(By.ID, 'create-post-options')
        self.assertFalse('hidden' in post_options.get_attribute('class'))
        
        # Check visibility selector is displayed
        selector = self.selenium.find_element(By.ID, 'visibility-selector')
        self.assertEqual(selector.value_of_css_property('display'), 'block') 