from django.urls import re_path

from messages.consumers import ConversationConsumer


websocket_urlpatterns = [
    re_path(r"^ws/messages/conversations/(?P<conversation_id>[0-9a-f-]+)/$", ConversationConsumer.as_asgi()),
]

