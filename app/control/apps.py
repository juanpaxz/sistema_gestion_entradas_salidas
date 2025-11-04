from django.apps import AppConfig


class ControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'control'
    
    def ready(self):
        # Import signals to ensure they are registered when the app is ready
        try:
            import control.signals  # noqa: F401
        except Exception:
            # Avoid breaking startup if signals cannot be imported during some operations
            pass
