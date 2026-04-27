from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsRescuer(BasePermission):
    message = "Only rescuer users can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "is_rescuer", False))


class IsPetOwnerOrAdmin(BasePermission):
    message = "You can only manage your own pet listings."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                getattr(user, "is_superuser", False)
                or getattr(user, "is_admin_user", False)
                or obj.rescuer_id == user.id
            )
        )


class IsConversationParticipant(BasePermission):
    message = "Only conversation participants can access this conversation."

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                getattr(user, "is_superuser", False)
                or getattr(user, "is_admin_user", False)
                or obj.adopter_id == user.id
                or obj.pet.rescuer_id == user.id
            )
        )
