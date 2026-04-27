import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth.models import UserRole


class PetSpecies(models.TextChoices):
    DOG = "DOG", _("Dog")
    CAT = "CAT", _("Cat")
    BIRD = "BIRD", _("Bird")
    RABBIT = "RABBIT", _("Rabbit")
    OTHER = "OTHER", _("Other")


class PetGender(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    UNKNOWN = "UNKNOWN", _("Unknown")


class PetSize(models.TextChoices):
    SMALL = "SMALL", _("Small")
    MEDIUM = "MEDIUM", _("Medium")
    LARGE = "LARGE", _("Large")
    EXTRA_LARGE = "EXTRA_LARGE", _("Extra Large")


class PetStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    AVAILABLE = "AVAILABLE", _("Available")
    PENDING = "PENDING", _("Pending")
    ADOPTED = "ADOPTED", _("Adopted")
    ON_HOLD = "ON_HOLD", _("On Hold")
    ARCHIVED = "ARCHIVED", _("Archived")


class Pet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rescuer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pets",
        verbose_name=_("Rescuer"),
    )
    title = models.CharField(max_length=150, verbose_name=_("Title"))
    species = models.CharField(max_length=20, choices=PetSpecies.choices, verbose_name=_("Species"))
    breed = models.CharField(max_length=100, blank=True, verbose_name=_("Breed"))
    gender = models.CharField(
        max_length=16,
        choices=PetGender.choices,
        default=PetGender.UNKNOWN,
        verbose_name=_("Gender"),
    )
    age_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Age In Months"),
        help_text=_("Stored in months so pets can be filtered and sorted consistently."),
    )
    size = models.CharField(max_length=16, choices=PetSize.choices, blank=True, verbose_name=_("Size"))
    color = models.CharField(max_length=100, blank=True, verbose_name=_("Color"))
    vaccinated = models.BooleanField(default=False, verbose_name=_("Vaccinated"))
    sterilized = models.BooleanField(default=False, verbose_name=_("Sterilized"))
    medical_notes = models.TextField(blank=True, verbose_name=_("Medical Notes"))
    temperament = models.TextField(blank=True, verbose_name=_("Temperament"))
    story = models.TextField(blank=True, verbose_name=_("Story"))
    current_location = models.CharField(max_length=150, blank=True, verbose_name=_("Current Location"))
    rescue_location = models.CharField(max_length=150, blank=True, verbose_name=_("Rescue Location"))
    status = models.CharField(
        max_length=16,
        choices=PetStatus.choices,
        default=PetStatus.DRAFT,
        verbose_name=_("Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["rescuer", "status"]),
            models.Index(fields=["species", "status"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.rescuer and self.rescuer.role != UserRole.RESCUER:
            raise ValidationError({"rescuer": _("Only rescuer users can create pet listings.")})


class PetImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="images", verbose_name=_("Pet"))
    image_url = models.URLField(verbose_name=_("Image URL"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort Order"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["pet", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.pet.title} image #{self.sort_order}"


class PetInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="interests", verbose_name=_("Pet"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pet_interests",
        verbose_name=_("User"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["pet", "user"], name="unique_pet_interest_per_user"),
        ]
        indexes = [
            models.Index(fields=["pet", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} interested in {self.pet_id}"


class ConversationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    CLOSED = "CLOSED", _("Closed")


class AdoptionRequestStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REJECTED = "REJECTED", _("Rejected")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class AdoptionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="adoption_requests", verbose_name=_("Pet"))
    adopter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adoption_requests",
        verbose_name=_("Adopter"),
    )
    intention = models.CharField(max_length=255, verbose_name=_("Adoption Intention"))
    message = models.TextField(blank=True, verbose_name=_("Message"))
    status = models.CharField(
        max_length=16,
        choices=AdoptionRequestStatus.choices,
        default=AdoptionRequestStatus.PENDING,
        verbose_name=_("Status"),
    )
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Accepted At"))
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Rejected At"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["pet", "adopter"],
                condition=models.Q(status__in=["PENDING", "ACCEPTED"]),
                name="unique_open_adoption_request_per_pet_adopter",
            ),
        ]
        indexes = [
            models.Index(fields=["pet", "status"]),
            models.Index(fields=["adopter", "status"]),
        ]

    def __str__(self):
        return f"{self.adopter_id} request for {self.pet_id}"

    def clean(self):
        super().clean()
        if self.adopter and self.adopter.role != UserRole.ADOPTER:
            raise ValidationError({"adopter": _("Only adopter users can create adoption requests.")})
        if self.pet and self.pet.status == PetStatus.ADOPTED:
            raise ValidationError({"pet": _("Adopted pets cannot receive new requests.")})


class PetConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="conversations", verbose_name=_("Pet"))
    adopter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pet_conversations",
        verbose_name=_("Adopter"),
    )
    status = models.CharField(
        max_length=16,
        choices=ConversationStatus.choices,
        default=ConversationStatus.ACTIVE,
        verbose_name=_("Status"),
    )
    adoption_request = models.OneToOneField(
        AdoptionRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation",
        verbose_name=_("Adoption Request"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["pet", "adopter"], name="unique_pet_conversation_per_adopter"),
        ]
        indexes = [
            models.Index(fields=["pet", "status"]),
        ]

    def __str__(self):
        return f"{self.pet_id} conversation with {self.adopter_id}"

    def clean(self):
        super().clean()
        if self.adopter and self.adopter.role != UserRole.ADOPTER:
            raise ValidationError({"adopter": _("Only adopter users can be attached to pet conversations.")})


class PetMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        PetConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Conversation"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pet_messages",
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
