from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from app.utils.cloudinary import delete_image, upload_image
from auth.models import (
    AdminAction,
    AdminModule,
    UserRole,
)


User = get_user_model()


class ImageUploadOrURLField(serializers.Field):
    url_field = serializers.URLField(allow_blank=True, required=False)

    def to_internal_value(self, data):
        if data is None:
            return None
        if hasattr(data, "read") and hasattr(data, "name"):
            return data
        return self.url_field.run_validation(data)

    def to_representation(self, value):
        return value or ""


class UserSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="admin_profile.job_title", read_only=True)
    permissions = serializers.SerializerMethodField()

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
            "job_title",
            "permissions",
            "is_active",
            "date_joined",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "role",
            "status",
            "is_verified",
            "job_title",
            "permissions",
            "is_active",
            "date_joined",
            "created_at",
            "updated_at",
        )

    def get_permissions(self, obj):
        if not obj.is_admin_user:
            return []

        if obj.is_superuser:
            return [
                {
                    "module": module,
                    "actions": [action for action, _ in AdminAction.choices],
                }
                for module, _ in AdminModule.choices
            ]

        admin_profile = getattr(obj, "admin_profile", None)
        if not admin_profile:
            return []

        permissions = []
        for admin_permission in admin_profile.permissions.select_related("permission").all():
            permissions.append(
                {
                    "module": admin_permission.permission.module,
                    "actions": admin_permission.actions,
                }
            )
        return permissions


class UserUpdateSerializer(serializers.ModelSerializer):
    avatar = ImageUploadOrURLField(required=False, allow_null=True)
    cover = ImageUploadOrURLField(required=False, allow_null=True)
    avatar_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    cover_file = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "name",
            "username",
            "email",
            "phone",
            "avatar",
            "avatar_file",
            "cover",
            "cover_file",
            "bio",
            "location",
        )

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
        avatar = validated_data.pop("avatar", serializers.empty)
        cover = validated_data.pop("cover", serializers.empty)
        avatar_file = validated_data.pop("avatar_file", serializers.empty)
        cover_file = validated_data.pop("cover_file", serializers.empty)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        avatar_input = avatar_file if avatar_file is not serializers.empty else avatar
        cover_input = cover_file if cover_file is not serializers.empty else cover

        if avatar_input is not serializers.empty:
            instance.avatar = self._handle_image_upload(
                image_input=avatar_input,
                current_url=instance.avatar,
                folder=f"{settings.CLOUDINARY_FOLDER}/users/profile",
                public_id=self._build_image_public_id(instance, "avatar"),
            )

        if cover_input is not serializers.empty:
            instance.cover = self._handle_image_upload(
                image_input=cover_input,
                current_url=instance.cover,
                folder=f"{settings.CLOUDINARY_FOLDER}/users/profile",
                public_id=self._build_image_public_id(instance, "cover"),
            )

        instance.save()
        return instance

    def _handle_image_upload(self, image_input, current_url, folder, public_id):
        if image_input is None:
            if current_url:
                delete_image(image_url=current_url)
            return ""

        if not hasattr(image_input, "read"):
            return image_input

        if current_url:
            delete_image(image_url=current_url)
        upload = upload_image(image_input, folder=folder, public_id=public_id)
        return upload["url"]

    def _build_image_public_id(self, user, image_type):
        base_name = slugify(user.username or user.name or user.email or user.phone or f"user-{image_type}")
        return base_name or f"user-{image_type}-{uuid4().hex[:8]}"


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=(UserRole.ADOPTER, UserRole.RESCUER),
        default=UserRole.ADOPTER,
        required=False,
    )
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "role",
            "name",
            "username",
            "email",
            "phone",
            "password",
            "confirm_password",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not attrs.get("email") and not attrs.get("username"):
            raise serializers.ValidationError({"email": "Either email or username is required."})
        return attrs

    def validate_username(self, value):
        if value in (None, ""):
            return None
        username = value.strip().lower()
        if not username:
            return None
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return username

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    identifier = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = (data.get("identifier") or data.get("email") or data.get("username") or "").strip()
        password = data.get("password")

        if not identifier:
            raise serializers.ValidationError({"email": "Email or username is required."})

        user = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError({"error": "Invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"error": "User is disabled."})

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the current password."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
