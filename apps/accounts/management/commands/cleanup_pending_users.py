from django.core.management.base import BaseCommand
from accounts.models import PendingUser
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Cleans up all pending users'

    def handle(self, *args, **options):
        expired_users = PendingUser.objects.all()
        count = expired_users.count()
        expired_users.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} pending users'))