from rest_framework.permissions import BasePermission


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

