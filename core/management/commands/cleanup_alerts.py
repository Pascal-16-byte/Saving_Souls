from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.models import DistressAlert

class Command(BaseCommand):
    help = "Deletes old distress alerts older than the configured retention period"

    def handle(self, *args, **kwargs):
        retention_days = getattr(settings, 'DISTRESS_ALERT_RETENTION_DAYS', 7)
        threshold_date = timezone.now() - timedelta(days=retention_days)

        deleted_count, _ = DistressAlert.objects.filter(detected_at__lt=threshold_date).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Deleted {deleted_count} distress alerts older than {retention_days} days."
            )
        )