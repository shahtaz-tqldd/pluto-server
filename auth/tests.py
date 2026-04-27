from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from auth.bootstrap import sync_default_permissions
from auth.models import (
    AdminAction,
    AdminInvitation,
    AdminModule,
    AdminPermission,
    AdminProfile,
    Permission,
    User,
    UserRole,
    UserStatus,
)


class ClientRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_defaults_to_adopter(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "name": "Default Adopter",
                "email": "default-adopter@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="default-adopter@example.com")
        self.assertEqual(user.role, UserRole.ADOPTER)
        self.assertTrue(hasattr(user, "adopter_profile"))
        self.assertEqual(response.data["data"]["role"], UserRole.ADOPTER)

    def test_register_can_create_rescuer(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "role": UserRole.RESCUER,
                "name": "Rescue User",
                "email": "rescuer-signup@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="rescuer-signup@example.com")
        self.assertEqual(user.role, UserRole.RESCUER)
        self.assertTrue(hasattr(user, "rescuer_profile"))
        self.assertEqual(response.data["data"]["role"], UserRole.RESCUER)

    def test_register_rejects_admin_role(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "role": UserRole.ADMIN,
                "name": "Public Admin",
                "email": "public-admin@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="public-admin@example.com").exists())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AdminInvitationFlowTests(TestCase):
    def setUp(self):
        sync_default_permissions()
        self.client = APIClient()
        self.superadmin_user = User.objects.create_superuser(
            email="superadmin@example.com",
            password="Password123!",
            name="Super Admin",
        )
        self.admin_user = User.objects.create_user(
            email="owner@example.com",
            password="Password123!",
            name="Owner Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
            is_active=True,
        )
        self.client.force_authenticate(self.admin_user)

    def test_admin_invitation_can_be_sent_and_redeemed(self):
        invite_response = self.client.post(
            "/api/v1/auth/admin/invitations/",
            {
                "email": "new-admin@example.com",
                "job_title": "Operations Lead",
                "permissions": [
                    {"module": AdminModule.PRODUCT_MANAGEMENT, "actions": [AdminAction.UPDATE]},
                    {"module": AdminModule.ORDER_MANAGEMENT, "actions": [AdminAction.VIEW, AdminAction.UPDATE]},
                ],
            },
            format="json",
        )
        self.assertEqual(invite_response.status_code, 201)
        token = invite_response.data["data"]["token"]

        verify_response = self.client.get(f"/api/v1/auth/admin-invitations/verify/?token={token}")
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.data["data"]["email"], "new-admin@example.com")
        self.assertEqual(verify_response.data["data"]["job_title"], "Operations Lead")

        self.client.force_authenticate(user=None)
        register_response = self.client.post(
            "/api/v1/auth/admin-register/",
            {
                "token": token,
                "name": "New Admin",
                "phone": "+15551234567",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, 201)

        user = User.objects.get(email="new-admin@example.com")
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertEqual(user.status, UserStatus.ACTIVE)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.has_role_permission(AdminModule.PRODUCT_MANAGEMENT, AdminAction.UPDATE))
        self.assertTrue(user.has_role_permission(AdminModule.ORDER_MANAGEMENT, AdminAction.VIEW))
        self.assertFalse(user.has_role_permission(AdminModule.CUSTOMER_MANAGEMENT, AdminAction.DELETE))

        invitation = AdminInvitation.objects.get(email="new-admin@example.com")
        self.assertIsNotNone(invitation.accepted_at)

        admin_profile = AdminProfile.objects.get(user=user)
        self.assertEqual(admin_profile.job_title, "Operations Lead")
        order_permission = AdminPermission.objects.get(
            admin_profile=admin_profile,
            permission__module=AdminModule.ORDER_MANAGEMENT,
        )
        self.assertIn(AdminAction.UPDATE, order_permission.actions)

    def test_default_permissions_are_seeded(self):
        modules = set(Permission.objects.values_list("module", flat=True))
        self.assertEqual(modules, {choice[0] for choice in AdminModule.choices})

    def test_invitation_cannot_be_used_twice(self):
        invitation = AdminInvitation.objects.create(
            email="twice@example.com",
            expires_at=timezone.now() + timedelta(hours=2),
            invited_by=self.admin_user,
        )
        token = invitation.issue_token()

        self.client.force_authenticate(user=None)
        first_register_response = self.client.post(
            "/api/v1/auth/admin-register/",
            {
                "token": token,
                "name": "Twice Admin",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            format="json",
        )
        self.assertEqual(first_register_response.status_code, 201)

        second_register_response = self.client.post(
            "/api/v1/auth/admin-register/",
            {
                "token": token,
                "name": "Twice Admin",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            format="json",
        )
        self.assertEqual(second_register_response.status_code, 400)
        self.assertIn("token", second_register_response.data["errors"])

    def test_superadmin_can_list_admin_users_with_permissions(self):
        self.client.force_authenticate(self.superadmin_user)

        listed_admin = User.objects.create_user(
            email="listed-admin@example.com",
            password="Password123!",
            name="Listed Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
            is_active=True,
        )
        admin_profile = AdminProfile.objects.create(
            user=listed_admin,
            job_title="Support Lead",
            assigned_by=self.superadmin_user,
            is_active=True,
        )
        order_permission = Permission.objects.get(module=AdminModule.ORDER_MANAGEMENT)
        chat_permission = Permission.objects.get(module=AdminModule.CHAT_SUPPORT)
        AdminPermission.objects.create(
            admin_profile=admin_profile,
            permission=order_permission,
            actions=[AdminAction.VIEW, AdminAction.UPDATE],
            granted_by=self.superadmin_user,
        )
        AdminPermission.objects.create(
            admin_profile=admin_profile,
            permission=chat_permission,
            actions=[AdminAction.VIEW],
            granted_by=self.superadmin_user,
        )

        response = self.client.get("/api/v1/auth/admin/admin-users/")

        self.assertEqual(response.status_code, 200)
        admins = response.data["data"]
        target = next(item for item in admins if item["email"] == "listed-admin@example.com")
        self.assertEqual(target["job_title"], "Support Lead")
        self.assertFalse(target["is_superuser"])
        self.assertEqual(
            target["permissions"],
            [
                {"module": AdminModule.ORDER_MANAGEMENT, "actions": [AdminAction.VIEW, AdminAction.UPDATE]},
                {"module": AdminModule.CHAT_SUPPORT, "actions": [AdminAction.VIEW]},
            ],
        )

    def test_regular_admin_cannot_list_admin_users(self):
        response = self.client.get("/api/v1/auth/admin/admin-users/")
        self.assertEqual(response.status_code, 403)

    def test_superadmin_can_update_admin_user_permissions(self):
        self.client.force_authenticate(self.superadmin_user)

        managed_admin = User.objects.create_user(
            email="managed-admin@example.com",
            password="Password123!",
            name="Managed Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
            is_active=True,
        )
        admin_profile = AdminProfile.objects.create(
            user=managed_admin,
            job_title="Old Title",
            assigned_by=self.superadmin_user,
            is_active=True,
        )
        product_permission = Permission.objects.get(module=AdminModule.PRODUCT_MANAGEMENT)
        AdminPermission.objects.create(
            admin_profile=admin_profile,
            permission=product_permission,
            actions=[AdminAction.VIEW],
            granted_by=self.superadmin_user,
        )

        response = self.client.patch(
            f"/api/v1/auth/admin/admin-users/{managed_admin.id}/",
            {
                "job_title": "New Title",
                "permissions": [
                    {"module": AdminModule.ORDER_MANAGEMENT, "actions": [AdminAction.VIEW, AdminAction.UPDATE]},
                    {"module": AdminModule.CHAT_SUPPORT, "actions": [AdminAction.VIEW]},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        managed_admin.refresh_from_db()
        self.assertEqual(managed_admin.admin_profile.job_title, "New Title")
        self.assertFalse(managed_admin.has_role_permission(AdminModule.PRODUCT_MANAGEMENT, AdminAction.VIEW))
        self.assertTrue(managed_admin.has_role_permission(AdminModule.ORDER_MANAGEMENT, AdminAction.UPDATE))
        self.assertTrue(managed_admin.has_role_permission(AdminModule.CHAT_SUPPORT, AdminAction.VIEW))

    def test_superadmin_can_delete_admin_user(self):
        self.client.force_authenticate(self.superadmin_user)

        managed_admin = User.objects.create_user(
            email="delete-admin@example.com",
            password="Password123!",
            name="Delete Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
            is_active=True,
        )
        AdminProfile.objects.create(
            user=managed_admin,
            job_title="Delete Me",
            assigned_by=self.superadmin_user,
            is_active=True,
        )

        response = self.client.delete(f"/api/v1/auth/admin/admin-users/{managed_admin.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=managed_admin.id).exists())

    def test_superadmin_cannot_delete_self(self):
        self.client.force_authenticate(self.superadmin_user)

        response = self.client.delete(f"/api/v1/auth/admin/admin-users/{self.superadmin_user.id}/")

        self.assertEqual(response.status_code, 400)

    def test_me_returns_permissions_for_admin_user(self):
        admin_profile = AdminProfile.objects.create(
            user=self.admin_user,
            job_title="Operations Lead",
            assigned_by=self.superadmin_user,
            is_active=True,
        )
        product_permission = Permission.objects.get(module=AdminModule.PRODUCT_MANAGEMENT)
        AdminPermission.objects.create(
            admin_profile=admin_profile,
            permission=product_permission,
            actions=[AdminAction.VIEW, AdminAction.UPDATE],
            granted_by=self.superadmin_user,
        )

        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["job_title"], "Operations Lead")
        self.assertEqual(
            response.data["data"]["permissions"],
            [
                {
                    "module": AdminModule.PRODUCT_MANAGEMENT,
                    "actions": [AdminAction.VIEW, AdminAction.UPDATE],
                }
            ],
        )

    def test_me_returns_full_permissions_for_superadmin(self):
        self.client.force_authenticate(self.superadmin_user)

        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["permissions"]), len(AdminModule.choices))
        self.assertEqual(
            response.data["data"]["permissions"][0]["actions"],
            [choice[0] for choice in AdminAction.choices],
        )
