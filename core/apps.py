from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
            from .models import Category
            from . import signals
            default_categories = ["Anxiety", "Depression", "Stress", "Loneliness", "Burnout", "Grief"]
            for name in default_categories:
                        Category.objects.get_or_create(name=name)