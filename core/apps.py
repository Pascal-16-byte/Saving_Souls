from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from . import signals
        # Import signals to ensure they're registered
        # Category creation will be handled by a data migration or management command

