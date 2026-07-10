from pathlib import Path
import environ
import os

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Path to .env file
env_path = BASE_DIR / '.env'

# Read the .env file
environ.Env.read_env(env_path)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Application definition
INSTALLED_APPS = [
    'app_1.apps.App1Config',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
        # Extensions - installed with pip3 / requirements.txt
    'django_extensions',
    'crispy_forms',
    'rest_framework',
    'social_django',
    'taggit',
    'corsheaders',
    'channels'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:8000',
])

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "https://llama.cnu.ac.kr",
    "http://localhost:3000",
    "http://127.0.0.1:8000"
])

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'project_1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'react_frontend' / 'build'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project_1.wsgi.application'
ASGI_APPLICATION = "project_1.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Configure session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# Secure cookies are disabled by default so local (http) dev works; production.py
# flips SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE on for HTTPS.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = True  # Helps mitigate against XSS attacks
SESSION_COOKIE_SAMESITE = 'Lax'  # Adjust as needed for your requirements

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOG_LEVEL = env('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'debug.log'),
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    # Capture all three of the project's own loggers (Django app, FastAPI agent,
    # and project config), not just app_1.
    'loggers': {
        name: {
            'handlers': ['file', 'console'],
            'level': LOG_LEVEL,
            'propagate': False,  # Prevent duplicate records via the root logger
        }
        for name in ('app_1', 'fastapi_agent', 'project_1')
    },
}

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# Static Files Configuration
# The Vite build (react_frontend/build) is emitted with base '/static/', so its
# hashed assets live in build/assets and are served under STATIC_URL. Run
# `yarn build` before `collectstatic`.
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'react_frontend' / 'build',  # Vite build output (index.html + assets/)
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Directory for collectstatic

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
