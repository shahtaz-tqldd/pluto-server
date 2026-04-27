from rest_framework.permissions import BasePermission


class IsAdopter(BasePermission):
    message = "Only adopter users can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "is_adopter", False))

