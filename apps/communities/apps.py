from django.apps import AppConfig


class CommunitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communities'
    verbose_name = 'Communities'
    
    def ready(self):
        import apps.communities.signals 