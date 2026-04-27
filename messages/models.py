import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth.models import UserRole


class ConversationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    CLOSED = "CLOSED", _("Closed")


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(
        "pluto_pets.Pet",
        on_delete=models.CASCADE,
        related_name="message_threads",
        verbose_name=_("Pet"),
    )
    adopter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_threads",
        verbose_name=_("Adopter"),
    )
    status = models.CharField(
        max_length=16,
        choices=ConversationStatus.choices,
        default=ConversationStatus.ACTIVE,
        verbose_name=_("Status"),
    )
    adoption_request = models.OneToOneField(
        "pluto_pets.AdoptionRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_thread",
        verbose_name=_("Adoption Request"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["pet", "adopter"], name="unique_message_conversation_per_adopter"),
        ]
        indexes = [
            models.Index(fields=["pet", "status"]),
        ]

    def __str__(self):
        return f"{self.pet_id} conversation with {self.adopter_id}"

    def clean(self):
        super().clean()
        if self.adopter and self.adopter.role != UserRole.ADOPTER:
            raise ValidationError({"adopter": _("Only adopter users can be attached to conversations.")})


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Conversation"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name=_("Sender"),
    )
    body = models.TextField(verbose_name=_("Body"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.sender_id} -> {self.conversation_id}"

    def clean(self):
        super().clean()
        if not self.conversation_id or not self.sender_id:
            return
        participants = {self.conversation.adopter_id, self.conversation.pet.rescuer_id}
        if self.sender_id not in participants:
            raise ValidationError({"sender": _("Only conversation participants can send messages.")})

