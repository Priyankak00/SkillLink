from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Example URL: ws://127.0.0.1:8000/ws/chat/1/
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/auction/$', consumers.AuctionConsumer.as_asgi()),
]