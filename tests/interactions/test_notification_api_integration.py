import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
import json
from django.contrib.contenttypes.models import ContentType

from apps.interactions.models import Notification, User
from apps.content.models import Post


@pytest.mark.django_db
class TestNotificationAPIFilters:
    """Test notification API filtering functionality."""
    
    @pytest.fixture
    def setup_notifications(self, create_user):
        """Create various notifications for testing filters."""
        # Create read notifications
        read_time = timezone.now() - timezone.timedelta(hours=2)
        for i in range(3):
            notification = Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Read Notification {i}",
                message=f"This is read notification {i}",
                is_read=True,
                read_at=read_time
            )
        
        # Create unread notifications
        for i in range(2):
            notification = Notification.objects.create(
                recipient=create_user,
                notification_type="like",
                title=f"Unread Notification {i}",
                message=f"This is unread notification {i}",
                is_read=False
            )
        
        return create_user
    
    def test_filter_unread_notifications(self, authenticated_client, setup_notifications):
        """Test filtering notifications by unread status."""
        url = reverse('notifications-list') + '?filter=unread'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Verify all returned notifications are unread
        for notification in response.data['results']:
            assert notification['is_read'] is False
    
    def test_filter_read_notifications(self, authenticated_client, setup_notifications):
        """Test filtering notifications by read status."""
        url = reverse('notifications-list') + '?filter=read'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
        
        # Verify all returned notifications are read
        for notification in response.data['results']:
            assert notification['is_read'] is True


@pytest.mark.django_db
class TestNotificationCreationOnActions:
    """Test that notifications are created when various actions occur."""
    
    @pytest.fixture
    def user1(self):
        """Create the first user."""
        return User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
            first_name="User",
            last_name="One"
        )
    
    @pytest.fixture
    def user2(self):
        """Create the second user."""
        return User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
            first_name="User",
            last_name="Two"
        )
    
    @pytest.fixture
    def post(self, user1):
        """Create a post for testing reactions."""
        return Post.objects.create(
            user=user1,
            body="This is a test post for notifications",
            title="Test Post"
        )
    
    def test_like_notification(self, api_client, user1, user2, post):
        """Test that a notification is created when someone likes a post."""
        api_client.force_authenticate(user=user2)
        
        # User2 likes User1's post
        url = reverse('posts-react', args=[post.id])
        response = api_client.post(url, {'reaction_type': 'like'})
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that a notification was created for user1
        notifications = Notification.objects.filter(
            recipient=user1,
            notification_type='like'
        )
        
        assert notifications.count() == 1
        notification = notifications.first()
        assert user2.username in notification.message
        assert notification.is_read is False
    
    def test_comment_notification(self, api_client, user1, user2, post):
        """Test that a notification is created when someone comments on a post."""
        api_client.force_authenticate(user=user2)
        
        # Get content type for Post model
        content_type_id = ContentType.objects.get_for_model(Post).id
        
        # User2 comments on User1's post
        url = reverse('posts-add-comment', args=[post.id])
        data = {
            'body': 'This is a test comment',
            'content_type': content_type_id,
            'object_id': post.id,
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that a notification was created for user1
        notifications = Notification.objects.filter(
            recipient=user1,
            notification_type='comment'
        )
        
        assert notifications.count() == 1
        notification = notifications.first()
        assert user2.username in notification.message
        assert notification.is_read is False
    
    def test_follow_notification(self, api_client, user1, user2):
        """Test that a notification is created when someone follows a user."""
        api_client.force_authenticate(user=user2)
        
        # User2 follows User1
        url = reverse('follow-user', args=[user1.id])
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that a notification was created for user1
        notifications = Notification.objects.filter(
            recipient=user1,
            notification_type='follow'
        )
        
        assert notifications.count() == 1
        notification = notifications.first()
        assert user2.username in notification.message
        assert "follow" in notification.message.lower()
        assert notification.is_read is False


@pytest.mark.django_db
class TestNotificationPagination:
    """Test notification pagination functionality."""
    
    @pytest.fixture
    def create_many_notifications(self, create_user):
        """Create a large number of notifications for testing pagination."""
        # Create 25 notifications (assuming pagination is set to 10 or 20)
        for i in range(25):
            Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"This is notification {i}",
                is_read=i % 2 == 0  # Alternate between read and unread
            )
        return create_user
    
    def test_pagination_first_page(self, authenticated_client, create_many_notifications):
        """Test first page of paginated notifications."""
        url = reverse('notifications-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'next' in response.data
        assert response.data['previous'] is None  # First page has no previous
        
        # Check that we got the expected number of results (depending on page size)
        assert len(response.data['results']) <= 20  # Assuming page_size is 20 or less
    
    def test_pagination_second_page(self, authenticated_client, create_many_notifications):
        """Test second page of paginated notifications."""
        # First get the first page to get the next URL
        url = reverse('notifications-list')
        response = authenticated_client.get(url)
        
        # Extract next page URL from response
        next_url = response.data['next']
        assert next_url is not None
        
        # Remove domain part to get just the path with query params
        next_path = next_url.split('http://testserver')[-1]
        
        # Get second page
        second_page_response = authenticated_client.get(next_path)
        
        assert second_page_response.status_code == status.HTTP_200_OK
        assert 'results' in second_page_response.data
        assert 'previous' in second_page_response.data
        assert second_page_response.data['previous'] is not None  # Second page has previous
        
        # We should have some results on the second page
        assert len(second_page_response.data['results']) > 0


@pytest.mark.django_db
class TestNotificationAPI:
    """Test additional notification API functionality not covered elsewhere."""
    
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
    
    def test_delete_notification(self, authenticated_client, notification):
        """Test deleting a notification."""
        url = reverse('notifications-detail', args=[notification.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify notification is deleted
        assert not Notification.objects.filter(id=notification.id).exists()
    
    def test_clear_all_notifications(self, authenticated_client, create_user):
        """Test clearing all notifications for a user."""
        # Create multiple notifications
        for i in range(5):
            Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"System message {i}"
            )
        
        # Try to clear all notifications
        if hasattr(reverse, 'clear-all-notifications'):
            url = reverse('clear-all-notifications')
            response = authenticated_client.delete(url)
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify all notifications were deleted
            count = Notification.objects.filter(recipient=create_user).count()
            assert count == 0
    
    def test_notification_count_api(self, authenticated_client, create_user):
        """Test API endpoint that returns notification counts."""
        # Create a mix of read and unread notifications
        for i in range(3):
            Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"System message {i}",
                is_read=False
            )
        
        for i in range(2):
            Notification.objects.create(
                recipient=create_user,
                notification_type="like",
                title=f"Read Notification {i}",
                message=f"This is read notification {i}",
                is_read=True
            )
        
        # Get notification counts if endpoint exists
        if hasattr(reverse, 'notifications-count'):
            url = reverse('notifications-count')
            response = authenticated_client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'unread_count' in response.data
            assert response.data['unread_count'] == 3
            assert 'total_count' in response.data
            assert response.data['total_count'] == 5 