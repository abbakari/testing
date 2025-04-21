from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/group/(?P<group_id>\d+)/chat/$', consumers.GroupChatConsumer.as_asgi()),
    re_path(r'ws/call/(?P<call_id>\d+)/$', consumers.GroupCallConsumer.as_asgi()),
]