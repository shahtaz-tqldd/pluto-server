from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from app.utils.response import APIResponse
from auth.api.v1.admin.serializers import (
    AdminInvitationCreateSerializer,
    AdminInvitationSerializer,
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    AdopterListSerializer,
    AdminInvitationRegistrationSerializer,
    AdminInvitationVerifySerializer,
)
from auth.models import User, UserRole
from auth.permissions import IsAdmin, IsSuperAdmin
from auth.services import assign_admin_access


class AdopterListAPIVIew(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdopterListSerializer

    def get_queryset(self):
        return User.objects.filter(role=UserRole.ADOPTER).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            data=serializer.data,
            message="Adopters fetched successfully.",
        )


class AdminInvitationCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminInvitationCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        output = AdminInvitationSerializer(
            invitation,
            context={"invite_payload": serializer.context.get("invite_payload")},
        )
        invite_payload = serializer.context.get("invite_payload") or {}
        response_data = {**output.data, "token": invite_payload.get("token")}
        return APIResponse.success(
            data=response_data,
            message="Admin invitation sent successfully.",
            status=status.HTTP_201_CREATED,
        )


class AdminUserListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        return (
            User.objects.filter(role=UserRole.ADMIN)
            .select_related("admin_profile")
            .prefetch_related("admin_profile__permissions__permission")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            data=serializer.data,
            message="Admin users fetched successfully.",
        )


class AdminUserManageAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminUserUpdateSerializer

    def get_object(self):
        return get_object_or_404(
            User.objects.select_related("admin_profile").prefetch_related("admin_profile__permissions__permission"),
            id=self.kwargs["admin_id"],
            role=UserRole.ADMIN,
        )

    def patch(self, request, *args, **kwargs):
        admin_user = self.get_object()

        if admin_user.is_superuser:
            return APIResponse.error(
                message="Superadmin users cannot be updated from this endpoint.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        current_permissions = []
        admin_profile = getattr(admin_user, "admin_profile", None)
        if admin_profile:
            for admin_permission in admin_profile.permissions.select_related("permission").all():
                current_permissions.append(
                    {
                        "module": admin_permission.permission.module,
                        "actions": admin_permission.actions,
                    }
                )

        permissions = serializer.validated_data.get("permissions", current_permissions)
        job_title = serializer.validated_data.get(
            "job_title",
            getattr(admin_profile, "job_title", ""),
        )

        assign_admin_access(
            user=admin_user,
            permissions=permissions,
            assigned_by=request.user,
            job_title=job_title,
        )

        admin_user = self.get_object()
        output = AdminUserListSerializer(admin_user)
        return APIResponse.success(
            data=output.data,
            message="Admin user updated successfully.",
        )

    def delete(self, request, *args, **kwargs):
        admin_user = self.get_object()

        if admin_user.is_superuser:
            return APIResponse.error(
                message="Superadmin users cannot be deleted from this endpoint.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if admin_user.id == request.user.id:
            return APIResponse.error(
                message="You cannot delete your own account.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        admin_user.delete()
        return APIResponse.success(message="Admin user deleted successfully.")

class AdminInvitationVerifyView(APIView):
    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token", "").strip()
        if not token:
            return APIResponse.error(
                errors={"token": ["Invitation token is required."]},
                message="Invalid invitation token.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation = resolve_admin_invitation(token)
        except ValidationError as exc:
            return APIResponse.error(
                errors={"token": [str(exc)]},
                message="Invitation verification failed.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminInvitationVerifySerializer(invitation)
        return APIResponse.success(
            data=serializer.data,
            message="Invitation verified successfully.",
        )


class AdminInvitationRegistrationView(GenericAPIView):
    serializer_class = AdminInvitationRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return APIResponse.success(
            data={
                "user": UserSerializer(result["user"]).data,
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
            },
            message="Admin account created successfully.",
            status=status.HTTP_201_CREATED,
        )
