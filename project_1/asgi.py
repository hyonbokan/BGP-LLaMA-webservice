import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application
import app_1.routing  # our custom websocket routes

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_1.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(  # adds Django session support to websockets
        AuthMiddlewareStack(             # adds authentication support
            URLRouter(
                app_1.routing.websocket_urlpatterns
            )
        )
    ),
})
