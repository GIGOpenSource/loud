"""
ASGI config for Pet project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# 延迟导入WebSocket路由，避免在Django应用加载前导入模型
def get_websocket_urlpatterns():
    from games.routing import websocket_urlpatterns
    return websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        get_websocket_urlpatterns()
    ),
})
