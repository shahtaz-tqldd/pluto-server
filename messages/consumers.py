from django.db.models import Q
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from messages.models import Conversation, ConversationStatus, Message


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conversation_{self.conversation_id}"

        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return

        if not await self._is_participant(user.id, self.conversation_id):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "message":
            await self.send_json({"error": "Unsupported event type."})
            return

        body = (content.get("body") or "").strip()
        if not body:
            await self.send_json({"error": "Message body cannot be empty."})
            return

        payload = await self._create_message(
            conversation_id=self.conversation_id,
            sender_id=self.scope["user"].id,
            body=body,
        )
        if payload is None:
            await self.send_json({"error": "Cannot send messages to a closed conversation."})
            return
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "message": payload},
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message", "data": event["message"]})

    @database_sync_to_async
    def _is_participant(self, user_id, conversation_id):
        return Conversation.objects.filter(
            id=conversation_id,
        ).filter(
            Q(adopter_id=user_id) | Q(pet__rescuer_id=user_id)
        ).exists()

    @database_sync_to_async
    def _create_message(self, conversation_id, sender_id, body):
        conversation = Conversation.objects.select_related("pet", "pet__rescuer", "adopter").get(id=conversation_id)
        if conversation.status != ConversationStatus.ACTIVE:
            return None
        message = Message.objects.create(
            conversation=conversation,
            sender_id=sender_id,
            body=body,
        )
        sender = message.sender
        return {
            "id": str(message.id),
            "conversation_id": str(conversation.id),
            "sender": str(sender.id),
            "sender_name": sender.name,
            "sender_role": sender.role,
            "body": message.body,
            "created_at": message.created_at.isoformat(),
        }
