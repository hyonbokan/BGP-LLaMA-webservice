from django.apps import AppConfig
import logging

class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_1'

    def ready(self):
        if not hasattr(self, 'models_initialized'):
            try:
                self.models_initialized = True
                logging.info("Model loaded successfully at server startup.")
            except Exception as e:
                logging.error(f"Failed to load the model at server startup: {str(e)}")
                raise e  # Re-raise the exception to prevent silent failures