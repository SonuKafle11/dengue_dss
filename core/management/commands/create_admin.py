"""
Usage:
  python manage.py create_admin --username admin --password admin123
"""
import hashlib
from django.core.management.base import BaseCommand
from core.models import AdminUser

class Command(BaseCommand):
    help = 'Create an admin user for the Dengue DSS admin panel'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin')
        parser.add_argument('--password', type=str, default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        hashed   = hashlib.sha256(password.encode()).hexdigest()

        obj, created = AdminUser.objects.update_or_create(
            username=username,
            defaults={'password': hashed}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Admin user "{username}" created successfully.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Admin user "{username}" already exists — password updated.'
            ))
        self.stdout.write(f'   Login at: /admin-login/')
        self.stdout.write(f'   Username: {username}')
        self.stdout.write(f'   Password: {password}')