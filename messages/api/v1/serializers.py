from rest_framework import serializers

from pets.api.v1.serializers import AdoptionRequestSerializer, PetFeedSerializer
from messages.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.name", read_only=True)
    sender_role = serializers.CharField(source="sender.role", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "sender_name", "sender_role", "body", "created_at")
        read_only_fields = fields


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("body",)

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message body cannot be empty.")
        return value

    def create(self, validated_data):
        conversation = self.context["conversation"]
        if conversation.status != "ACTIVE":
            raise serializers.ValidationError("Cannot send messages to a closed conversation.")
        return Message.objects.create(
            conversation=conversation,
            sender=self.context["request"].user,
            **validated_data,
        )


class ConversationSerializer(serializers.ModelSerializer):
    pet = PetFeedSerializer(read_only=True)
    adopter_name = serializers.CharField(source="adopter.name", read_only=True)
    rescuer_name = serializers.CharField(source="pet.rescuer.name", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    request = AdoptionRequestSerializer(source="adoption_request", read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "pet",
            "adopter",
            "adopter_name",
            "rescuer_name",
            "status",
            "request",
            "messages",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

