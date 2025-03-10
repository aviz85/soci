import time
from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apps.communities.models import Community
from apps.content.models import Post

User = get_user_model()

class UserJourneyTests(LiveServerTestCase):
    """Test a complete user journey through the application"""
    
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
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Create a test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='This is a test community',
            creator=self.other_user
        )
        
        # Create some test posts
        Post.objects.create(
            author=self.other_user,
            body='This is a test post',
            visibility='public'
        )
    
    def test_complete_user_journey(self):
        """Test a complete user journey through the application"""
        # Step 1: Navigate to login page
        self.selenium.get(f'{self.live_server_url}/login/')
        
        # Step 2: Login
        username_input = self.selenium.find_element(By.NAME, 'username')
        password_input = self.selenium.find_element(By.NAME, 'password')
        username_input.send_keys('testuser')
        password_input.send_keys('testpass123')
        password_input.send_keys(Keys.RETURN)
        
        # Wait for redirect to homepage
        WebDriverWait(self.selenium, 10).until(
            EC.url_to_be(f'{self.live_server_url}/')
        )
        
        # Step 3: Verify user is logged in
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.ID, 'user-name'), 'Test User')
        )
        
        # Step 4: Check feed loads
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'feed-container'))
        )
        
        # Step 5: Create a post
        post_input = self.selenium.find_element(By.ID, 'create-post-input')
        post_input.send_keys('This is a test post from the integration test')
        post_button = self.selenium.find_element(By.ID, 'create-post-btn')
        post_button.click()
        
        # Step 6: Wait for post to appear in feed
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.post-content'), 'This is a test post from the integration test')
        )
        
        # Step 7: Navigate to communities page
        communities_link = self.selenium.find_element(By.CSS_SELECTOR, '.main-nav a[href="/communities"]')
        communities_link.click()
        
        # Wait for communities page to load
        WebDriverWait(self.selenium, 10).until(
            EC.url_contains('/communities')
        )
        
        # Step 8: Check community listing
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.community-card'))
        )
        
        # Step 9: Log out
        user_button = self.selenium.find_element(By.CSS_SELECTOR, '.user-button')
        user_button.click()
        
        # Wait for dropdown to appear
        WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.user-dropdown'))
        )
        
        logout_button = self.selenium.find_element(By.ID, 'logout-button')
        logout_button.click()
        
        # Step 10: Verify redirect to login page
        WebDriverWait(self.selenium, 10).until(
            EC.url_contains('/login')
        )
        
        # Verify login form is visible
        self.assertTrue(self.selenium.find_element(By.NAME, 'username').is_displayed()) 