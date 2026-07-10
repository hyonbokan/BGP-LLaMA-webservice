from .base import *

DEBUG = False

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# --- Security hardening (behind Nginx/TLS) ---
# Nginx terminates TLS and forwards the original scheme in this header, so
# Django can tell HTTPS requests apart and avoid redirect loops.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

# Only send session/CSRF cookies over HTTPS in production.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS — tell browsers to only ever use HTTPS for this domain.
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Misc hardening.
SECURE_CONTENT_TYPE_NOSNIFF = True
