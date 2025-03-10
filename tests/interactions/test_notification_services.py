import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.interactions.models import Notification, Connection
from apps.content.models import Post, Comment

User = get_user_model()


@pytest.mark.django_db
class TestNotificationCreationServices:
    """Test notification creation in various scenarios."""
    
    @pytest.fixture
    def users(self):
        """Create users for testing."""
        user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123"
        )
        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123"
        )
        return user1, user2
    
    @pytest.fixture
    def post(self, users):
        """Create a post for testing."""
        user1, _ = users
        return Post.objects.create(
            user=user1,
            body="Test post content"
        )
    
    def test_follow_notification_creation(self, users):
        """Test notification creation when a user follows another."""
        user1, user2 = users
        
        # Create a connection (follow)
        connection = Connection.objects.create(
            follower=user1,
            followed=user2
        )
        
        # Check if notification was created
        notifications = Notification.objects.filter(
            recipient=user2,
            notification_type='follow'
        )
        assert notifications.exists()
        
        notification = notifications.first()
        assert user1.username in notification.message
        assert not notification.is_read
    
    def test_comment_notification_creation(self, users, post):
        """Test notification creation when a user comments on a post."""
        user1, user2 = users
        
        # Create a comment
        comment = Comment.objects.create(
            author=user2,
            post=post,
            content="This is a test comment"
        )
        
        # Check if notification was created
        notifications = Notification.objects.filter(
            recipient=user1,  # post author
            notification_type='comment'
        )
        assert notifications.exists()
        
        notification = notifications.first()
        assert user2.username in notification.message
        assert not notification.is_read
    
    def test_mention_notification_creation(self, users):
        """Test notification creation when a user mentions another."""
        user1, user2 = users
        
        # Create a post with mention
        post = Post.objects.create(
            user=user1,
            body=f"Hello @{user2.username} this is a mention test"
        )
        
        # Check if notification was created
        notifications = Notification.objects.filter(
            recipient=user2,
            notification_type='mention'
        )
        assert notifications.exists()
        
        notification = notifications.first()
        assert user1.username in notification.message
        assert not notification.is_read


@pytest.mark.django_db
class TestNotificationBulkOperations:
    """Test bulk operations on notifications."""
    
    @pytest.fixture
    def user_with_notifications(self):
        """Create a user with multiple notifications."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Create 5 notifications of different types
        types = ['follow', 'like', 'comment', 'mention', 'system']
        
        for i, notification_type in enumerate(types):
            Notification.objects.create(
                recipient=user,
                notification_type=notification_type,
                title=f"{notification_type.capitalize()} Notification",
                message=f"Test {notification_type} notification {i}"
            )
        
        return user
    
    def test_bulk_mark_as_read(self, user_with_notifications):
        """Test marking all notifications as read."""
        # Verify initial state
        assert Notification.objects.filter(
            recipient=user_with_notifications,
            is_read=False
        ).count() == 5
        
        # Mark all as read
        now = timezone.now()
        count = Notification.objects.filter(
            recipient=user_with_notifications,
            is_read=False
        ).update(is_read=True, read_at=now)
        
        assert count == 5
        assert Notification.objects.filter(
            recipient=user_with_notifications,
            is_read=True
        ).count() == 5
    
    def test_bulk_mark_by_type(self, user_with_notifications):
        """Test marking notifications of a specific type as read."""
        # Mark only follow notifications as read
        now = timezone.now()
        count = Notification.objects.filter(
            recipient=user_with_notifications,
            notification_type='follow',
            is_read=False
        ).update(is_read=True, read_at=now)
        
        assert count == 1
        assert Notification.objects.filter(
            recipient=user_with_notifications,
            is_read=True
        ).count() == 1
        assert Notification.objects.filter(
            recipient=user_with_notifications,
            is_read=False
        ).count() == 4
    
    def test_count_unread_notifications(self, user_with_notifications):
        """Test counting unread notifications."""
        # Mark some as read
        Notification.objects.filter(
            recipient=user_with_notifications,
            notification_type__in=['follow', 'like']
        ).update(is_read=True, read_at=timezone.now())
        
        # Count unread
        unread_count = Notification.objects.filter(
            recipient=user_with_notifications,
            is_read=False
        ).count()
        
        assert unread_count == 3
    
    def test_delete_old_notifications(self, user_with_notifications):
        """Test deleting old notifications."""
        # Set some notifications to old dates
        old_date = timezone.now() - timezone.timedelta(days=60)
        Notification.objects.filter(
            recipient=user_with_notifications,
            notification_type__in=['follow', 'like']
        ).update(created_at=old_date)
        
        # Delete notifications older than 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        deleted_count = Notification.objects.filter(
            created_at__lt=thirty_days_ago
        ).delete()[0]
        
        assert deleted_count == 2
        assert Notification.objects.count() == 3 