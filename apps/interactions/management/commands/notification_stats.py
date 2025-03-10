from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.interactions.models import Notification


class Command(BaseCommand):
    help = 'Show notification statistics'

    def handle(self, *args, **options):
        total_count = Notification.objects.count()
        read_count = Notification.objects.filter(is_read=True).count()
        unread_count = Notification.objects.filter(is_read=False).count()

        # Count by type
        type_counts = Notification.objects.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')

        self.stdout.write(self.style.SUCCESS(f"Total notifications: {total_count}"))
        self.stdout.write(self.style.SUCCESS(f"Read notifications: {read_count}"))
        self.stdout.write(self.style.SUCCESS(f"Unread notifications: {unread_count}"))
        self.stdout.write("\nNotifications by type:")
        
        for type_count in type_counts:
            notification_type = type_count['notification_type']
            count = type_count['count']
            self.stdout.write(f"  {notification_type}: {count}") 