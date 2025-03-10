import pytest
from django.core.management import call_command
from django.utils import timezone
from io import StringIO
from unittest.mock import patch

from apps.interactions.models import Notification


@pytest.mark.django_db
class TestNotificationManagementCommands:
    """Test management commands related to notifications."""
    
    @pytest.fixture
    def user_with_old_notifications(self, create_user):
        """Create a user with old notifications."""
        # Create recent notifications
        for i in range(3):
            Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Recent Notification {i}",
                message=f"Recent notification {i}"
            )
        
        # Create old notifications (90 days old)
        old_date = timezone.now() - timezone.timedelta(days=90)
        for i in range(5):
            notification = Notification.objects.create(
                recipient=create_user,
                notification_type="system",
                title=f"Old Notification {i}",
                message=f"Old notification {i}"
            )
            # Update created_at date
            Notification.objects.filter(id=notification.id).update(created_at=old_date)
        
        return create_user
    
    def test_clean_old_notifications_command(self, user_with_old_notifications):
        """Test the clean_old_notifications management command."""
        # Verify we have 8 notifications (3 recent + 5 old)
        assert Notification.objects.count() == 8
        
        # Call the command with 60 days threshold
        out = StringIO()
        call_command('clean_old_notifications', days=60, stdout=out)
        
        # Verify the old notifications are deleted
        assert Notification.objects.count() == 3  # Only the recent ones remain
        
        # Check command output
        output = out.getvalue()
        assert "Deleted 5 notifications" in output
    
    def test_clean_old_notifications_dry_run(self, user_with_old_notifications):
        """Test the clean_old_notifications command with dry run."""
        # Verify we have 8 notifications (3 recent + 5 old)
        assert Notification.objects.count() == 8
        
        # Call the command with dry run
        out = StringIO()
        call_command('clean_old_notifications', days=60, dry_run=True, stdout=out)
        
        # Verify no notifications were deleted
        assert Notification.objects.count() == 8
        
        # Check command output
        output = out.getvalue()
        assert "Would delete 5 notifications" in output
    
    def test_notification_stats_command(self, user_with_old_notifications):
        """Test the notification_stats management command."""
        # Mark some notifications as read
        Notification.objects.filter(title__startswith="Recent").update(is_read=True)
        
        # Call the command
        out = StringIO()
        call_command('notification_stats', stdout=out)
        
        # Check command output
        output = out.getvalue()
        assert "Total notifications: 8" in output
        assert "Read notifications: 3" in output
        assert "Unread notifications: 5" in output
    
    @patch('django.utils.timezone.now')
    def test_send_notification_reminders_command(self, mock_now, user_with_old_notifications):
        """Test the send_notification_reminders management command."""
        from datetime import datetime
        from django.utils.timezone import make_aware
        
        # Set current time
        mock_now.return_value = make_aware(datetime(2023, 1, 1, 12, 0, 0))
        
        # Set some notifications to be 3 days old
        three_days_ago = mock_now.return_value - timezone.timedelta(days=3)
        Notification.objects.filter(title__startswith="Recent Notification").update(
            created_at=three_days_ago,
            is_read=False
        )
        
        # Call the command with 2 days cutoff
        out = StringIO()
        call_command('send_notification_reminders', days=2, stdout=out)
        
        # Check command output
        output = out.getvalue()
        assert "Sending reminders for 3 unread notifications" in output
        
        # In a real test, we'd also check that emails were sent
        # but that requires mocking the email backend 