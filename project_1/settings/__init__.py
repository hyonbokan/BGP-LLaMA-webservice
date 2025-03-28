import os

env_mode = os.getenv('DJANGO_ENV', 'development')

if env_mode == 'production':
    from .production import *
else:
    from .development import *