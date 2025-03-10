import pytest
from django.utils import timezone

from apps.interactions.models import Notification
from apps.interactions.serializers import NotificationSerializer


@pytest.mark.django_db
class TestNotificationSerializer:
    """Test the NotificationSerializer."""
    
    def test_notification_serialization(self, create_user):
        """Test serializing a notification."""
        notification = Notification.objects.create(
            recipient=create_user,
            notification_type="follow",
            title="New Follower",
            message="Someone started following you",
            link="https://example.com/profile"
        )
        
        serializer = NotificationSerializer(notification)
        data = serializer.data
        
        assert data['id'] == notification.id
        assert data['notification_type'] == "follow"
        assert data['title'] == "New Follower"
        assert data['message'] == "Someone started following you"
        assert data['link'] == "https://example.com/profile"
        assert data['is_read'] is False
        assert data['read_at'] is None
        assert 'created_at' in data
        
        # Check that the recipient is serialized
        assert data['recipient']['id'] == create_user.id
        assert data['recipient']['username'] == create_user.username
    
    def test_notification_serialization_list(self, create_user):
        """Test serializing a list of notifications."""
        # Create multiple notifications
        notifications = []
        for i in range(3):
            notification = Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"System notification {i}"
            )
            notifications.append(notification)
        
        serializer = NotificationSerializer(notifications, many=True)
        data = serializer.data
        
        assert len(data) == 3
        for i, item in enumerate(data):
            assert item['id'] == notifications[i].id
            assert item['title'] == f"Notification {i}"
            assert item['message'] == f"System notification {i}"
    
    def test_serialization_with_read_status(self, create_user):
        """Test serializing notifications with different read statuses."""
        # Create unread notification
        unread = Notification.objects.create(
            recipient=create_user,
            notification_type="follow",
            title="Unread Notification",
            message="This is unread",
            is_read=False
        )
        
        # Create read notification
        read_time = timezone.now() - timezone.timedelta(hours=1)
        read = Notification.objects.create(
            recipient=create_user,
            notification_type="like",
            title="Read Notification",
            message="This is read",
            is_read=True,
            read_at=read_time
        )
        
        # Serialize both
        unread_serializer = NotificationSerializer(unread)
        read_serializer = NotificationSerializer(read)
        
        unread_data = unread_serializer.data
        read_data = read_serializer.data
        
        # Check unread notification
        assert unread_data['is_read'] is False
        assert unread_data['read_at'] is None
        
        # Check read notification
        assert read_data['is_read'] is True
        assert read_data['read_at'] is not None
    
    def test_serialization_ordering(self, create_user):
        """Test that notifications are ordered by created_at descending."""
        # Create notifications with different timestamps
        old_time = timezone.now() - timezone.timedelta(days=2)
        middle_time = timezone.now() - timezone.timedelta(days=1)
        recent_time = timezone.now()
        
        notification1 = Notification.objects.create(
            recipient=create_user,
            notification_type="follow",
            title="Old Notification",
            message="This is old",
            created_at=old_time
        )
        
        notification2 = Notification.objects.create(
            recipient=create_user,
            notification_type="like",
            title="Middle Notification",
            message="This is in the middle",
            created_at=middle_time
        )
        
        notification3 = Notification.objects.create(
            recipient=create_user,
            notification_type="comment",
            title="Recent Notification",
            message="This is recent",
            created_at=recent_time
        )
        
        # Get all notifications (should be in reverse chronological order)
        notifications = Notification.objects.all()
        serializer = NotificationSerializer(notifications, many=True)
        data = serializer.data
        
        # Check that the order is most recent first
        assert data[0]['id'] == notification3.id
        assert data[1]['id'] == notification2.id
        assert data[2]['id'] == notification1.id 