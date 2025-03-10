from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from apps.interactions.models import Notification


class Command(BaseCommand):
    help = 'Send email reminders for unread notifications'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=2,
                            help='Send reminders for notifications older than this many days')
        parser.add_argument('--dry-run', action='store_true',
                            help='Only show what would be sent')

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        # Calculate the cutoff date
        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        # Get unread notifications older than the cutoff date
        old_unread_notifications = Notification.objects.filter(
            is_read=False,
            created_at__lt=cutoff_date
        ).select_related('recipient')

        # Group by user
        user_notifications = {}
        for notification in old_unread_notifications:
            user = notification.recipient
            if user.email:  # Only include users with email addresses
                if user.id not in user_notifications:
                    user_notifications[user.id] = {
                        'user': user,
                        'notifications': []
                    }
                user_notifications[user.id]['notifications'].append(notification)

        # Send reminders
        count = old_unread_notifications.count()
        self.stdout.write(self.style.SUCCESS(f"Sending reminders for {count} unread notifications"))

        if not dry_run:
            for user_data in user_notifications.values():
                user = user_data['user']
                notifications = user_data['notifications']
                
                subject = f"You have {len(notifications)} unread notifications"
                
                message = f"Hello {user.username},\n\n"
                message += f"You have {len(notifications)} unread notifications at SociSphere that you might want to check.\n\n"
                
                for notification in notifications[:5]:  # Limit to 5 in the email
                    message += f"- {notification.title}: {notification.message}\n"
                
                if len(notifications) > 5:
                    message += f"\n...and {len(notifications) - 5} more.\n"
                    
                message += "\nVisit the site to view all your notifications.\n\n"
                message += "Best regards,\nThe SociSphere Team"
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    self.stdout.write(f"Sent reminder to {user.email}")
                except Exception as e:
                    self.stderr.write(f"Failed to send email to {user.email}: {str(e)}")
        else:
            self.stdout.write("Dry run - no emails sent") 