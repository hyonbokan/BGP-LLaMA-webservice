from django.apps import AppConfig


class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_1'
    
    def ready(self):
        from .model_loader import ModelContainer
        ModelContainer.load_model()