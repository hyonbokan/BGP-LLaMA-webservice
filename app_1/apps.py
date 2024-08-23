from django.apps import AppConfig
import logging

class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_1'
    
    def ready(self):
        from .model_loader import load_model
        try:
            load_model()
            logging.info("Model loaded successfully at server startup.")
        except Exception as e:
            logging.error(f"Failed to load the model at server startup: {str(e)}")
        