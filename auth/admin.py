from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from auth.models import (
    AdopterProfile,
    AdminInvitation,
    AdminPermission,
    AdminProfile,
    Permission,
    RescuerProfile,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = ("name", "email", "phone", "role", "status", "is_verified", "is_staff", "is_active")
    search_fields = ("name", "email", "phone", "location")
    readonly_fields = ("id", "date_joined", "created_at", "updated_at", "last_login")

    fieldsets = (
        ("Credentials", {"fields": ("email", "phone", "password")}),
        ("Profile", {"fields": ("name", "avatar", "bio", "location", "is_verified")}),
        ("Access", {"fields": ("role", "status", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone", "name", "password1", "password2", "role", "status"),
            },
        ),
    )


admin.site.register(AdopterProfile)
admin.site.register(AdminProfile)
admin.site.register(AdminInvitation)
admin.site.register(Permission)
admin.site.register(AdminPermission)
admin.site.register(RescuerProfile)
