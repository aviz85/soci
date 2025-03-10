import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.interactions.models import Notification
from apps.users.models import User


@pytest.mark.django_db
class TestNotificationViewSet:
    """Test the NotificationViewSet API endpoints."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123",
            first_name="Second",
            last_name="User"
        )
    
    @pytest.fixture
    def notifications_url(self):
        """Return the notifications list URL."""
        return reverse('notifications-list')
    
    @pytest.fixture
    def notification(self, create_user):
        """Create a test notification."""
        return Notification.objects.create(
            recipient=create_user,
            notification_type="follow",
            title="New follower",
            message="User started following you!",
            link="https://example.com/profile"
        )
    
    def test_list_notifications_authenticated(self, authenticated_client, notification, notifications_url):
        """Test retrieving notifications when authenticated."""
        response = authenticated_client.get(notifications_url)
        
        assert response.status_code == status.HTTP_200_OK
        # The API uses pagination, so we need to check the results
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == notification.id
        assert response.data['results'][0]['notification_type'] == notification.notification_type
        assert response.data['results'][0]['title'] == notification.title
        assert not response.data['results'][0]['is_read']
    
    def test_list_notifications_unauthenticated(self, api_client, notification, notifications_url):
        """Test retrieving notifications when not authenticated."""
        response = api_client.get(notifications_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_notifications_empty(self, authenticated_client, notifications_url):
        """Test retrieving notifications when there are none."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        response = authenticated_client.get(notifications_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 0
    
    def test_mark_notification_as_read(self, authenticated_client, notification):
        """Test marking a notification as read."""
        url = reverse('notifications-mark-read', args=[notification.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == "notification marked as read"
        
        # Check that the notification was updated in the database
        notification.refresh_from_db()
        assert notification.is_read
        assert notification.read_at is not None
    
    def test_mark_all_notifications_as_read(self, authenticated_client, create_user):
        """Test marking all notifications as read."""
        # Create multiple notifications
        for i in range(3):
            Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"System notification {i}",
            )
        
        url = reverse('mark-all-notifications-read')
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert response.data['status'] == "all notifications marked as read"
        
        # Check that all notifications were updated in the database
        unread_count = Notification.objects.filter(
            recipient=create_user, 
            is_read=False
        ).count()
        assert unread_count == 0
    
    def test_other_user_cannot_view_notifications(self, api_client, notification, second_user, notifications_url):
        """Test that users cannot view notifications of other users."""
        api_client.force_authenticate(user=second_user)
        response = api_client.get(notifications_url)
        
        # Should return an empty list, not other user's notifications
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 0
    
    def test_other_user_cannot_mark_notification_read(self, api_client, notification, second_user):
        """Test that users cannot mark other users' notifications as read."""
        api_client.force_authenticate(user=second_user)
        url = reverse('notifications-mark-read', args=[notification.id])
        response = api_client.post(url)
        
        # Should return 404 as the notification isn't accessible to this user
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Notification should still be unread
        notification.refresh_from_db()
        assert not notification.is_read


@pytest.mark.django_db
class TestNotificationCreation:
    """Test scenarios that create notifications."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123",
            first_name="Second",
            last_name="User"
        )
    
    def test_follow_creates_notification(self, authenticated_client, create_user, second_user):
        """Test that following a user creates a notification."""
        # Follow the second user
        url = reverse('follow-user', args=[second_user.id])
        authenticated_client.post(url)
        
        # Check if a notification was created for the second user
        notifications = Notification.objects.filter(
            recipient=second_user,
            notification_type='follow'
        )
        assert notifications.count() == 1
        notification = notifications.first()
        assert notification.title == 'New Follower'
        assert create_user.username in notification.message 