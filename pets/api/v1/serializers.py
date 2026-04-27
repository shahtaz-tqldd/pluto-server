from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from app.utils.cloudinary import delete_image, upload_image
from messages.models import Conversation, Message
from pets.models import AdoptionRequest, AdoptionRequestStatus, Pet, PetImage, PetInterest


class PetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetImage
        fields = ("id", "image_url", "sort_order")
        read_only_fields = fields


class PetSerializer(serializers.ModelSerializer):
    images = PetImageSerializer(many=True, read_only=True)
    rescuer_name = serializers.CharField(source="rescuer.name", read_only=True)
    primary_image = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    interested_count = serializers.IntegerField(read_only=True)
    active_conversation_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pet
        fields = (
            "id",
            "rescuer",
            "rescuer_name",
            "title",
            "species",
            "breed",
            "gender",
            "age_months",
            "age",
            "size",
            "color",
            "vaccinated",
            "sterilized",
            "medical_notes",
            "temperament",
            "story",
            "current_location",
            "rescue_location",
            "status",
            "primary_image",
            "interested_count",
            "active_conversation_count",
            "images",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "rescuer", "rescuer_name", "images", "created_at", "updated_at")

    def get_primary_image(self, obj):
        first_image = next(iter(getattr(obj, "images").all()), None)
        return first_image.image_url if first_image else ""

    def get_age(self, obj):
        if obj.age_months is None:
            return ""
        if obj.age_months < 12:
            return f"{obj.age_months} month{'s' if obj.age_months != 1 else ''}"

        years = obj.age_months // 12
        months = obj.age_months % 12
        if months:
            return f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"
        return f"{years} year{'s' if years != 1 else ''}"


class PetFeedSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    interested_count = serializers.IntegerField(read_only=True)
    active_conversation_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pet
        fields = (
            "id",
            "title",
            "species",
            "breed",
            "gender",
            "age_months",
            "age",
            "size",
            "current_location",
            "status",
            "primary_image",
            "interested_count",
            "active_conversation_count",
            "created_at",
        )
        read_only_fields = fields

    def get_primary_image(self, obj):
        first_image = next(iter(getattr(obj, "images").all()), None)
        return first_image.image_url if first_image else ""

    def get_age(self, obj):
        return PetSerializer(context=self.context).get_age(obj)


class PetWriteSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    remove_image_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Pet
        fields = (
            "title",
            "species",
            "breed",
            "gender",
            "age_months",
            "size",
            "color",
            "vaccinated",
            "sterilized",
            "medical_notes",
            "temperament",
            "story",
            "current_location",
            "rescue_location",
            "status",
            "images",
            "remove_image_ids",
        )

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if self.instance is None and not getattr(user, "is_rescuer", False):
            raise serializers.ValidationError("Only rescuer users can create or manage pet listings.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        image_files = validated_data.pop("images", [])
        pet = Pet.objects.create(rescuer=self.context["request"].user, **validated_data)
        self._upload_images(pet, image_files)
        return pet

    @transaction.atomic
    def update(self, instance, validated_data):
        image_files = validated_data.pop("images", [])
        remove_image_ids = validated_data.pop("remove_image_ids", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if remove_image_ids:
            self._remove_images(instance, remove_image_ids)
        if image_files:
            self._upload_images(instance, image_files)

        return instance

    def _upload_images(self, pet, image_files):
        if not image_files:
            return

        next_sort_order = (pet.images.order_by("-sort_order").values_list("sort_order", flat=True).first() or -1) + 1
        for file_obj in image_files:
            upload = upload_image(
                file_obj,
                folder=f"{settings.CLOUDINARY_FOLDER}/pets",
                public_id=f"{slugify(pet.title) or 'pet'}-{next_sort_order}",
            )
            PetImage.objects.create(
                pet=pet,
                image_url=upload["url"],
                sort_order=next_sort_order,
            )
            next_sort_order += 1

    def _remove_images(self, pet, image_ids):
        images = list(pet.images.filter(id__in=image_ids))
        for image in images:
            delete_image(image_url=image.image_url)
            image.delete()


class PetInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetInterest
        fields = ("id", "pet", "user", "created_at")
        read_only_fields = fields


class AdoptionRequestSerializer(serializers.ModelSerializer):
    adopter_name = serializers.CharField(source="adopter.name", read_only=True)
    adopter_email = serializers.CharField(source="adopter.email", read_only=True)
    adopter_phone = serializers.CharField(source="adopter.phone", read_only=True)
    adopter_avatar = serializers.CharField(source="adopter.avatar", read_only=True)
    adopter_location = serializers.CharField(source="adopter.location", read_only=True)
    adopter_profile = serializers.SerializerMethodField()
    pet_summary = PetFeedSerializer(source="pet", read_only=True)
    conversation_id = serializers.SerializerMethodField()

    class Meta:
        model = AdoptionRequest
        fields = (
            "id",
            "pet",
            "pet_summary",
            "adopter",
            "adopter_name",
            "adopter_email",
            "adopter_phone",
            "adopter_avatar",
            "adopter_location",
            "adopter_profile",
            "intention",
            "message",
            "status",
            "conversation_id",
            "accepted_at",
            "rejected_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_adopter_profile(self, obj):
        profile = getattr(obj.adopter, "adopter_profile", None)
        if not profile:
            return None
        return {
            "home_type": profile.home_type,
            "pet_experience": profile.pet_experience,
            "preferred_pet_type": profile.preferred_pet_type,
        }

    def get_conversation_id(self, obj):
        conversation = getattr(obj, "message_thread", None)
        return str(conversation.id) if conversation else None


class AdoptionRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdoptionRequest
        fields = ("intention", "message")

    def validate(self, attrs):
        pet = self.context["pet"]
        user = self.context["request"].user
        if pet.status != "AVAILABLE":
            raise serializers.ValidationError("Only available pets can receive adoption requests.")
        if pet.rescuer_id == user.id:
            raise serializers.ValidationError("You cannot request adoption for your own pet listing.")
        return attrs

    def create(self, validated_data):
        pet = self.context["pet"]
        adopter = self.context["request"].user
        request_obj = AdoptionRequest.objects.create(pet=pet, adopter=adopter, **validated_data)
        PetInterest.objects.get_or_create(pet=pet, user=adopter)
        return request_obj


class AdoptionRequestActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("accept", "reject"))


class PetMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.name", read_only=True)
    sender_role = serializers.CharField(source="sender.role", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "sender_name", "sender_role", "body", "created_at")
        read_only_fields = fields


class PetConversationSerializer(serializers.ModelSerializer):
    pet = PetFeedSerializer(read_only=True)
    adopter_name = serializers.CharField(source="adopter.name", read_only=True)
    rescuer_name = serializers.CharField(source="pet.rescuer.name", read_only=True)
    messages = PetMessageSerializer(many=True, read_only=True)
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
