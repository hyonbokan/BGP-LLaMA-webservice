import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack
import app_1.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_1.settings")

application = ProtocolTypeRouter({
    "websocket": SessionMiddlewareStack(
        AuthMiddlewareStack(
            URLRouter(app_1.routing.websocket_urlpatterns)
        )
    ),
})
