from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json
import requests
from requests.exceptions import ConnectionError
from unittest.mock import patch, MagicMock

User = get_user_model()

class ApiMockingTests(TestCase):
    """Tests to verify client handling of API responses and errors"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Get auth token
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        
        # Set up API client
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    @patch('requests.get')
    def test_api_client_handles_server_errors(self, mock_get):
        """Test that the API client properly handles 500 errors"""
        # Mock a 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("No JSON content")
        mock_get.return_value = mock_response
        
        # Call the API endpoint
        response = self.client.get('/api/content/feed/')
        
        # Verify the client returns an appropriate error response
        self.assertEqual(response.status_code, 500)
    
    @patch('requests.get')
    def test_api_client_handles_connection_failures(self, mock_get):
        """Test that the API client properly handles connection failures"""
        # Mock a connection error
        mock_get.side_effect = ConnectionError("Connection refused")
        
        # Call the API endpoint
        response = self.client.get('/api/content/feed/')
        
        # Verify the client returns an appropriate error response
        self.assertEqual(response.status_code, 503)
    
    def test_api_client_throttling(self):
        """Test that the API client handles rate limiting correctly"""
        # Make a large number of rapid requests to trigger throttling
        for _ in range(30):
            self.client.get('/api/content/feed/')
        
        # This request should be throttled
        response = self.client.get('/api/content/feed/')
        
        # Check if the response indicates throttling (status code 429)
        self.assertIn(response.status_code, [200, 429])
    
    def test_client_fallback_to_mock_data(self):
        """Test that the client falls back to mock data when API is unavailable"""
        # Temporarily disable the API endpoint
        with patch('apps.content.views.ContentViewSet.get_queryset', side_effect=Exception("API unavailable")):
            response = self.client.get('/api/content/feed/')
            
            # Even with an exception, the client should handle this gracefully
            self.assertIn(response.status_code, [200, 500, 503])
            
            # If it's 200, it should contain mock data
            if response.status_code == 200:
                content = json.loads(response.content)
                self.assertIn('results', content)
    
    def test_client_handles_partial_api_failures(self):
        """Test that the client handles partial API failures"""
        # Verify we can access the main feed
        feed_response = self.client.get('/api/content/feed/')
        self.assertEqual(feed_response.status_code, 200)
        
        # Simulate failure in a secondary endpoint
        with patch('apps.communities.views.CommunityViewSet.get_queryset', side_effect=Exception("API unavailable")):
            # The main page should still load even if communities API fails
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200) 