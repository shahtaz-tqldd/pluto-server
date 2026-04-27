from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from app.utils.response import APIResponse
from messages.api.v1.serializers import ConversationSerializer, MessageCreateSerializer
from messages.models import Conversation
from messages.permissions import IsConversationParticipant


class ConversationDetailAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def get_object(self):
        conversation = get_object_or_404(
            Conversation.objects.select_related("pet", "pet__rescuer", "adopter", "adoption_request")
            .prefetch_related("pet__images", "messages__sender"),
            id=self.kwargs["conversation_id"],
        )
        self.check_object_permissions(self.request, conversation)
        return conversation

    def get(self, request, *args, **kwargs):
        return APIResponse.success(
            data=ConversationSerializer(self.get_object()).data,
            message="Conversation fetched successfully.",
        )


class ConversationMessageListCreateAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def get_object(self):
        conversation = get_object_or_404(
            Conversation.objects.select_related("pet", "pet__rescuer", "adopter", "adoption_request")
            .prefetch_related("pet__images", "messages__sender"),
            id=self.kwargs["conversation_id"],
        )
        self.check_object_permissions(self.request, conversation)
        return conversation

    def get(self, request, *args, **kwargs):
        conversation = self.get_object()
        return APIResponse.success(
            data=ConversationSerializer(conversation).data["messages"],
            message="Messages fetched successfully.",
        )

    def post(self, request, *args, **kwargs):
        conversation = self.get_object()
        serializer = MessageCreateSerializer(
            data=request.data,
            context={"request": request, "conversation": conversation},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        conversation.refresh_from_db()
        return APIResponse.success(
            data=ConversationSerializer(conversation).data,
            message="Message sent successfully.",
            status=status.HTTP_201_CREATED,
        )
