from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from auth.models import (
    AdminAction,
    AdminModule,
    UserRole,
)


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="admin_profile.job_title", read_only=True)
    permissions = serializers.SerializerMethodField()

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
    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "phone",
            "avatar",
            "bio",
            "location",
        )

    def validate(self, attrs):
        email = attrs.get("email", self.instance.email if self.instance else None)
        phone = attrs.get("phone", self.instance.phone if self.instance else None)
        if not email and not phone:
            raise serializers.ValidationError({"email": "Either email or phone is required."})
        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


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
            "email",
            "phone",
            "password",
            "confirm_password",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not attrs.get("email") and not attrs.get("phone"):
            raise serializers.ValidationError({"email": "Either email or phone is required."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        request = self.context.get("request")

        user = authenticate(request=request, email=email, password=password)

        if not user:
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
