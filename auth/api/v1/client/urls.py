from django.urls import path

from auth.api.v1.client.views import (
    ChangePasswordView,
    CreateNewUserView,
    LoginView,
    RefreshTokenView,
    UserDetailsUpdateView,
    UserDetailsView,
)


urlpatterns = [
    path("register/", CreateNewUserView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh-token"),
    path("user-details/", UserDetailsView.as_view(), name="user-details"),
    path("user-details/update/", UserDetailsUpdateView.as_view(), name="update-user"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
