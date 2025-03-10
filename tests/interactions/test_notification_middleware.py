import pytest
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

from apps.interactions.models import Notification
from apps.interactions.middleware import NotificationMiddleware


class MockResponse(HttpResponse):
    """Mock response for testing."""
    def __init__(self):
        super().__init__()
        self.context_data = {}


class MockTemplateResponse:
    """Mock template response for testing."""
    def __init__(self):
        self.context_data = {}
        self.is_rendered = False

    def render(self):
        self.is_rendered = True


@pytest.mark.django_db
class TestNotificationMiddleware:
    """Test the notification middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Return an instance of the notification middleware."""
        return NotificationMiddleware(get_response=lambda request: MockResponse())
    
    @pytest.fixture
    def request_factory(self):
        """Return a request factory."""
        return RequestFactory()
    
    @pytest.fixture
    def user_with_notifications(self, create_user):
        """Create a user with notifications."""
        # Create unread notifications
        for i in range(3):
            Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"System notification {i}"
            )
        
        # Create read notifications
        for i in range(2):
            Notification.objects.create(
                recipient=create_user,
                notification_type="follow",
                title=f"Read Notification {i}",
                message=f"This is read {i}",
                is_read=True
            )
        
        return create_user
    
    def test_middleware_with_authenticated_user(self, middleware, request_factory, user_with_notifications):
        """Test middleware with an authenticated user."""
        request = request_factory.get('/')
        request.user = user_with_notifications
        
        response = middleware(request)
        
        # Check that context contains notification count
        assert 'unread_notifications_count' in response.context_data
        assert response.context_data['unread_notifications_count'] == 3
    
    def test_middleware_with_anonymous_user(self, middleware, request_factory):
        """Test middleware with an anonymous user."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        
        response = middleware(request)
        
        # Check that context doesn't have notification data
        assert 'unread_notifications_count' not in response.context_data
    
    def test_middleware_with_template_response(self, middleware, request_factory, user_with_notifications):
        """Test middleware with a template response."""
        request = request_factory.get('/')
        request.user = user_with_notifications
        
        # Create a template response
        response = MockTemplateResponse()
        
        # Call the process_template_response method
        processed = middleware.process_template_response(request, response)
        
        # Check that context contains notification count
        assert 'unread_notifications_count' in processed.context_data
        assert processed.context_data['unread_notifications_count'] == 3
        
        # Check that the original response was returned
        assert processed is response
    
    def test_middleware_with_ajax_request(self, middleware, request_factory, user_with_notifications):
        """Test middleware with an AJAX request."""
        request = request_factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = user_with_notifications
        
        response = middleware(request)
        
        # AJAX requests may not process template context
        assert 'unread_notifications_count' not in response.context_data 