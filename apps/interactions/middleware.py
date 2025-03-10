from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser

from apps.interactions.models import Notification


class NotificationMiddleware:
    """
    Middleware to add notification data to the response context.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process the request and add notification data to response context."""
        response = self.get_response(request)
        
        # For non-template responses, we need to add context_data
        if not hasattr(response, 'context_data'):
            response.context_data = {}
        
        # Add unread notification count to the context for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            response.context_data['unread_notifications_count'] = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        
        return response
    
    def process_template_response(self, request, response):
        """Add notification data to template responses."""
        # Add unread notification count to the context for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            response.context_data['unread_notifications_count'] = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
            
        return response 