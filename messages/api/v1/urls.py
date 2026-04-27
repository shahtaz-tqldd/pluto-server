from django.urls import path

from messages.api.v1.views import ConversationDetailAPIView, ConversationMessageListCreateAPIView


urlpatterns = [
    path("conversations/<uuid:conversation_id>/", ConversationDetailAPIView.as_view(), name="conversation-detail"),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ConversationMessageListCreateAPIView.as_view(),
        name="conversation-messages",
    ),
]

