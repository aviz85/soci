import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class ClientLoadingTests(TestCase):
    """Tests for client-side loading functionality"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create authenticated client
        self.client = Client()
        self.api_client = APIClient()
        
        # Get auth token for API requests
        refresh = RefreshToken.for_user(self.user)
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_home_page_loads(self):
        """Test home page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        
    def test_static_files_load(self):
        """Test that critical static files load correctly"""
        # Check main CSS file
        css_response = self.client.get('/static/css/main.css')
        self.assertEqual(css_response.status_code, 200)
        self.assertEqual(css_response['Content-Type'], 'text/css')
        
        # Check main JS file
        js_response = self.client.get('/static/js/main.js')
        self.assertEqual(js_response.status_code, 200)
        self.assertEqual(js_response['Content-Type'], 'application/javascript')
        
        # Check API JS file
        api_js_response = self.client.get('/static/js/api.js')
        self.assertEqual(api_js_response.status_code, 200)
        self.assertEqual(api_js_response['Content-Type'], 'application/javascript')
        
        # Check default avatar
        avatar_response = self.client.get('/static/img/default-avatar.svg')
        self.assertEqual(avatar_response.status_code, 200)
        self.assertEqual(avatar_response['Content-Type'], 'image/svg+xml')
    
    def test_api_endpoints_authenticated(self):
        """Test that API endpoints respond correctly when authenticated"""
        # Test user profile endpoint
        profile_response = self.api_client.get('/api/users/me/')
        self.assertEqual(profile_response.status_code, 200)
        data = json.loads(profile_response.content)
        self.assertEqual(data['username'], 'testuser')
        
        # Test notifications endpoint
        notifications_response = self.api_client.get('/api/interactions/notifications/')
        self.assertEqual(notifications_response.status_code, 200)
        
        # Test communities endpoint
        communities_response = self.api_client.get('/api/communities/')
        self.assertEqual(communities_response.status_code, 200)
        
        # Test feed endpoint
        feed_response = self.api_client.get('/api/content/feed/')
        self.assertEqual(feed_response.status_code, 200)
    
    def test_api_endpoints_unauthenticated(self):
        """Test that API endpoints require authentication"""
        unauthenticated_client = APIClient()
        
        # Test user profile endpoint
        profile_response = unauthenticated_client.get('/api/users/me/')
        self.assertEqual(profile_response.status_code, 401)
        
        # Test notifications endpoint
        notifications_response = unauthenticated_client.get('/api/interactions/notifications/')
        self.assertEqual(notifications_response.status_code, 401)
        
        # Test communities endpoint
        communities_response = unauthenticated_client.get('/api/communities/')
        self.assertEqual(communities_response.status_code, 401)
        
        # Test feed endpoint
        feed_response = unauthenticated_client.get('/api/content/feed/')
        self.assertEqual(feed_response.status_code, 401)

    def test_login_page_loads(self):
        """Test login page loads successfully"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html') 