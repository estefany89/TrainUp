from django.apps import AppConfig


class GimnasioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gimnasio'

    def ready(self):
        import gimnasio.signals  # Esto asegura que la señal se registre
