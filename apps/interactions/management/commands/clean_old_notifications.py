from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.interactions.models import Notification


class Command(BaseCommand):
    help = 'Clean old notifications that are older than the specified number of days'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30,
                            help='Delete notifications older than this many days')
        parser.add_argument('--dry-run', action='store_true',
                            help='Only show what would be deleted')

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        # Calculate the cutoff date
        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        # Get notifications older than the cutoff date
        old_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
        count = old_notifications.count()

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Would delete {count} notifications older than {days} days")
            )
        else:
            old_notifications.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {count} notifications older than {days} days")
            ) 