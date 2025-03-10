import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Resets the database by removing it and recreating it'

    def handle(self, *args, **kwargs):
        self.stdout.write('Resetting database...')
        
        # Get the path to the SQLite database file
        db_path = settings.DATABASES['default']['NAME']
        
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                self.stdout.write(self.style.SUCCESS(f'Successfully removed database file at {db_path}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to remove database file: {e}'))
                return
        else:
            self.stdout.write(f'Database file not found at {db_path}, will create a new one.')
        
        # Run migrations
        from django.core.management import call_command
        call_command('migrate')
        
        self.stdout.write(self.style.SUCCESS('Successfully reset database and applied migrations')) 