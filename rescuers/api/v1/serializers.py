from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from app.utils.cloudinary import delete_image, upload_image
from auth.models import RescuerProfile, RescuerVerificationStatus
from messages.api.v1.serializers import ConversationSerializer
from pets.api.v1.serializers import AdoptionRequestSerializer, PetFeedSerializer, PetSerializer
from pets.models import AdoptionRequest, Pet
from rescuers.models import RescuerReview


User = get_user_model()


class RescuerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RescuerProfile
        fields = (
            "organization_name",
            "experience_years",
            "verification_status",
            "successful_adoptions",
            "response_rate",
        )
        read_only_fields = ("verification_status", "successful_adoptions", "response_rate")


class RescuerAccountSerializer(serializers.ModelSerializer):
    rescuer_profile = RescuerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "role",
            "name",
            "username",
            "email",
            "phone",
            "avatar",
            "cover",
            "bio",
            "location",
            "is_verified",
            "status",
            "rescuer_profile",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class RescuerAccountUpdateSerializer(serializers.ModelSerializer):
    avatar_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    cover_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    organization_name = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, min_value=0)
    verification_status = serializers.ChoiceField(choices=RescuerVerificationStatus.choices, required=False)
    successful_adoptions = serializers.IntegerField(required=False, min_value=0)
    response_rate = serializers.DecimalField(required=False, max_digits=5, decimal_places=2, min_value=0, max_value=100)

    class Meta:
        model = User
        fields = (
            "name",
            "username",
            "email",
            "phone",
            "bio",
            "location",
            "avatar",
            "avatar_file",
            "cover",
            "cover_file",
            "organization_name",
            "experience_years",
            "verification_status",
            "successful_adoptions",
            "response_rate",
        )
        read_only_fields = ("avatar", "cover")

    def validate_username(self, value):
        if value in (None, ""):
            return None
        username = value.strip().lower()
        if not username:
            return None
        queryset = User.objects.filter(username__iexact=username)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return username

    def validate(self, attrs):
        email = attrs.get("email", self.instance.email if self.instance else None)
        username = attrs.get("username", self.instance.username if self.instance else None)
        phone = attrs.get("phone", self.instance.phone if self.instance else None)
        if not email and not username and not phone:
            raise serializers.ValidationError({"email": "Either email, username, or phone is required."})
        return attrs

    def update(self, instance, validated_data):
        avatar_file = validated_data.pop("avatar_file", serializers.empty)
        cover_file = validated_data.pop("cover_file", serializers.empty)
        profile_data = {
            key: validated_data.pop(key)
            for key in (
                "organization_name",
                "experience_years",
                "verification_status",
                "successful_adoptions",
                "response_rate",
            )
            if key in validated_data
        }

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if avatar_file is not serializers.empty:
            instance.avatar = self._handle_image_upload(
                image_file=avatar_file,
                current_url=instance.avatar,
                folder=f"{settings.CLOUDINARY_FOLDER}/users/rescuers",
                public_id=self._build_image_public_id(instance, "avatar"),
            )

        if cover_file is not serializers.empty:
            instance.cover = self._handle_image_upload(
                image_file=cover_file,
                current_url=instance.cover,
                folder=f"{settings.CLOUDINARY_FOLDER}/users/rescuers",
                public_id=self._build_image_public_id(instance, "cover"),
            )

        instance.save()
        instance.ensure_role_profile()
        if profile_data:
            RescuerProfile.objects.update_or_create(user=instance, defaults=profile_data)
        return instance

    def _handle_image_upload(self, image_file, current_url, folder, public_id):
        if image_file is None:
            if current_url:
                delete_image(image_url=current_url)
            return ""

        if current_url:
            delete_image(image_url=current_url)
        upload = upload_image(image_file, folder=folder, public_id=public_id)
        return upload["url"]

    def _build_image_public_id(self, user, image_type):
        base_name = slugify(user.username or user.name or user.email or user.phone or f"rescuer-{image_type}")
        return base_name or f"rescuer-{image_type}-{uuid4().hex[:8]}"


class RescuerPetSerializer(PetSerializer):
    class Meta(PetSerializer.Meta):
        fields = PetSerializer.Meta.fields


class RescuerDashboardSerializer(serializers.Serializer):
    rescuer = RescuerAccountSerializer()
    pets = RescuerPetSerializer(many=True)

    def to_representation(self, instance):
        return {
            "rescuer": RescuerAccountSerializer(instance["rescuer"]).data,
            "pets": RescuerPetSerializer(instance["pets"], many=True).data,
        }


class RescuerAdoptionRequestSerializer(AdoptionRequestSerializer):
    pass


class RescuerConversationSerializer(ConversationSerializer):
    pass


class RescuerReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    author_avatar = serializers.CharField(source="author.avatar", read_only=True)
    author_role = serializers.CharField(source="author.role", read_only=True)

    class Meta:
        model = RescuerReview
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


class RescuerReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RescuerReview
        fields = ("rating", "message")

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        rescuer = self.context["rescuer"]
        user = request.user
        if user.id == rescuer.id:
            raise serializers.ValidationError("You cannot review yourself.")
        if getattr(user, "role", "") not in {"ADOPTER", "ADMIN"}:
            raise serializers.ValidationError("Only adopters or admins can leave rescuer reviews.")
        return attrs

    def create(self, validated_data):
        return RescuerReview.objects.create(
            rescuer=self.context["rescuer"],
            author=self.context["request"].user,
            **validated_data,
        )


class PublicRescuerSummarySerializer(serializers.ModelSerializer):
    rescuer_profile = RescuerProfileSerializer(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "username",
            "avatar",
            "cover",
            "bio",
            "location",
            "is_verified",
            "rescuer_profile",
            "review_count",
            "average_rating",
        )
        read_only_fields = fields


class PublicRescuerProfileSerializer(serializers.Serializer):
    rescuer = PublicRescuerSummarySerializer()
    rescued_pet_list = PetFeedSerializer(many=True)
    current_available_pets = PetFeedSerializer(many=True)
    adopted_pet_history = PetFeedSerializer(many=True)
    reviews = RescuerReviewSerializer(many=True)
    trust_indicators = serializers.DictField()

    def to_representation(self, instance):
        rescuer = instance["rescuer"]
        return {
            "rescuer": PublicRescuerSummarySerializer(rescuer).data,
            "rescued_pet_list": PetFeedSerializer(instance["rescued_pet_list"], many=True).data,
            "current_available_pets": PetFeedSerializer(instance["current_available_pets"], many=True).data,
            "adopted_pet_history": PetFeedSerializer(instance["adopted_pet_history"], many=True).data,
            "reviews": RescuerReviewSerializer(instance["reviews"], many=True).data,
            "trust_indicators": instance["trust_indicators"],
        }
