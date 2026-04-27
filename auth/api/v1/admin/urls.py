from django.urls import path

from auth.api.v1.admin.views import (
    AdminInvitationCreateAPIView,
    AdminUserListAPIView,
    AdminUserManageAPIView,
    AdopterListAPIVIew,
    AdminInvitationRegistrationView,
    AdminInvitationVerifyView,
)


urlpatterns = [
    path("adopter/list/", AdopterListAPIVIew.as_view(), name="adopter-list"),

    # admin users
    path("admin-users/", AdminUserListAPIView.as_view(), name="admin-user-list"),
    path("admin-users/<uuid:admin_id>/", AdminUserManageAPIView.as_view(), name="admin-user-manage"),
    path("send-invitation/", AdminInvitationCreateAPIView.as_view(), name="admin-invitation-create"),
    path("verify-invitation/", AdminInvitationVerifyView.as_view(), name="admin-invitation-verify"),
    path("admin-register/", AdminInvitationRegistrationView.as_view(), name="admin-register"),
]
