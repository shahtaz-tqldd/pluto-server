from django.contrib.auth import get_user_model
from uuid import uuid4

from django.conf import settings
from django.utils.text import slugify
from rest_framework import serializers

from app.utils.cloudinary import delete_image, upload_image
from auth.models import AdopterProfile
from adopters.models import AdopterReview
from messages.api.v1.serializers import ConversationSerializer
from pets.api.v1.serializers import (
    AdoptionRequestCreateSerializer,
    AdoptionRequestSerializer,
    PetFeedSerializer,
)
User = get_user_model()


class AdopterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdopterProfile
        fields = ("home_type", "pet_experience", "preferred_pet_type")


class AdopterAccountSerializer(serializers.ModelSerializer):
    adopter_profile = AdopterProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "role",
            "name",
            "email",
            "phone",
            "avatar",
            "bio",
            "location",
            "is_verified",
            "status",
            "adopter_profile",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AdopterAccountUpdateSerializer(serializers.ModelSerializer):
    avatar_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    home_type = serializers.CharField(required=False, allow_blank=True)
    pet_experience = serializers.CharField(required=False, allow_blank=True)
    preferred_pet_type = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "phone",
            "bio",
            "location",
            "avatar",
            "avatar_file",
            "home_type",
            "pet_experience",
            "preferred_pet_type",
        )
        read_only_fields = ("avatar",)

    def validate(self, attrs):
        email = attrs.get("email", self.instance.email if self.instance else None)
        phone = attrs.get("phone", self.instance.phone if self.instance else None)
        if not email and not phone:
            raise serializers.ValidationError({"email": "Either email or phone is required."})
        return attrs

    def update(self, instance, validated_data):
        avatar_file = validated_data.pop("avatar_file", serializers.empty)
        profile_data = {
            key: validated_data.pop(key)
            for key in ("home_type", "pet_experience", "preferred_pet_type")
            if key in validated_data
        }

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if avatar_file is not serializers.empty:
            if avatar_file is None:
                if instance.avatar:
                    delete_image(image_url=instance.avatar)
                instance.avatar = ""
            else:
                if instance.avatar:
                    delete_image(image_url=instance.avatar)
                upload = upload_image(
                    avatar_file,
                    folder=f"{settings.CLOUDINARY_FOLDER}/users/adopters",
                    public_id=self._build_avatar_public_id(instance),
                )
                instance.avatar = upload["url"]

        instance.save()
        instance.ensure_role_profile()
        if profile_data:
            AdopterProfile.objects.update_or_create(user=instance, defaults=profile_data)
        return instance

    def _build_avatar_public_id(self, user):
        base_name = slugify(user.name or user.email or user.phone or "adopter-avatar")
        return base_name or f"adopter-avatar-{uuid4().hex[:8]}"


class AdopterAdoptionRequestCreateSerializer(AdoptionRequestCreateSerializer):
    pass


class AdopterAdoptionRequestSerializer(AdoptionRequestSerializer):
    pass


class AdopterConversationSerializer(ConversationSerializer):
    pass


class AdopterReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    author_avatar = serializers.CharField(source="author.avatar", read_only=True)
    author_role = serializers.CharField(source="author.role", read_only=True)

    class Meta:
        model = AdopterReview
        fields = (
            "id",
            "author",
            "author_name",
            "author_avatar",
            "author_role",
            "rating",
            "message",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AdopterReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdopterReview
        fields = ("rating", "message")

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        adopter = self.context["adopter"]
        user = request.user
        if user.id == adopter.id:
            raise serializers.ValidationError("You cannot review yourself.")
        if getattr(user, "role", "") not in {"RESCUER", "ADMIN"}:
            raise serializers.ValidationError("Only rescuers or admins can leave adopter reviews.")
        return attrs

    def create(self, validated_data):
        return AdopterReview.objects.create(
            adopter=self.context["adopter"],
            author=self.context["request"].user,
            **validated_data,
        )


class PublicAdopterSummarySerializer(serializers.ModelSerializer):
    adopter_profile = AdopterProfileSerializer(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "avatar",
            "bio",
            "location",
            "is_verified",
            "adopter_profile",
            "review_count",
            "average_rating",
        )
        read_only_fields = fields


class PublicAdopterProfileSerializer(serializers.Serializer):
    adopter = PublicAdopterSummarySerializer()
    adoption_activity = serializers.ListField()
    adopted_pet_history = serializers.ListField()
    reviews = AdopterReviewSerializer(many=True)
    trust_indicators = serializers.DictField()

    def to_representation(self, instance):
        adopter = instance["adopter"]
        return {
            "adopter": PublicAdopterSummarySerializer(adopter).data,
            "adoption_activity": AdoptionRequestSerializer(instance["adoption_activity"], many=True).data,
            "adopted_pet_history": PetFeedSerializer(instance["adopted_pet_history"], many=True).data,
            "reviews": AdopterReviewSerializer(instance["reviews"], many=True).data,
            "trust_indicators": instance["trust_indicators"],
        }
