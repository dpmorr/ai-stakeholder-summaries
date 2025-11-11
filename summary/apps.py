"""App configuration for summary service."""

from django.apps import AppConfig


class SummaryConfig(AppConfig):
    """Configuration for the summary app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'summary'
    verbose_name = 'Summary Generation'

    def ready(self):
        """Initialize app when Django starts."""
        # Import signal handlers if needed
        pass
