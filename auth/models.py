import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


phone_regex = RegexValidator(
    regex=r"^\+?1?\d{6,15}$",
    message=_("Phone number must be between 6 and 15 digits and may start with '+'."),
)


def validate_bio_word_limit(value):
    if value and len(value.split()) > 80:
        raise ValidationError(_("Bio cannot exceed 80 words."))


class UserRole(models.TextChoices):
    ADOPTER = "ADOPTER", _("Adopter")
    RESCUER = "RESCUER", _("Rescuer")
    ADMIN = "ADMIN", _("Admin")


class UserStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    SUSPENDED = "SUSPENDED", _("Suspended")
    BLOCKED = "BLOCKED", _("Blocked")


class RescuerVerificationStatus(models.TextChoices):
    UNVERIFIED = "UNVERIFIED", _("Unverified")
    PENDING = "PENDING", _("Pending")
    VERIFIED = "VERIFIED", _("Verified")
    REJECTED = "REJECTED", _("Rejected")


class AdminModule(models.TextChoices):
    PET_LISTING_MANAGEMENT = "PET_LISTING_MANAGEMENT", _("Pet Listing Management")
    USER_MANAGEMENT = "USER_MANAGEMENT", _("User Management")
    ADOPTION_MANAGEMENT = "ADOPTION_MANAGEMENT", _("Adoption Management")


class AdminAction(models.TextChoices):
    VIEW = "VIEW", _("View")
    CREATE = "CREATE", _("Create")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email=None, password=None, **extra_fields):
        phone = extra_fields.get("phone")
        username = extra_fields.get("username")
        if not email and not username and not phone:
            raise ValueError("Either email, username, or phone is required.")

        if email:
            email = self.normalize_email(email)
        if username:
            extra_fields["username"] = username.strip().lower()

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        user.ensure_role_profile()
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", UserRole.ADOPTER)
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("name", "Super Admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if not email:
            raise ValueError("Superuser must have an email address.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=16,
        choices=UserRole.choices,
        default=UserRole.ADOPTER,
        verbose_name=_("User Role"),
    )
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    username = models.CharField(
        unique=True,
        max_length=150,
        null=True,
        blank=True,
        verbose_name=_("Username"),
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Email Address"),
        help_text=_("Optional for now, but required if email-based login is used."),
    )
    phone = models.CharField(
        validators=[phone_regex],
        unique=True,
        max_length=17,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
    )
    avatar = models.URLField(blank=True, verbose_name=_("Avatar URL"))
    cover = models.URLField(blank=True, verbose_name=_("Cover URL"))
    bio = models.TextField(blank=True, validators=[validate_bio_word_limit], verbose_name=_("Bio"))
    location = models.CharField(max_length=120, blank=True, verbose_name=_("Location"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified"))
    status = models.CharField(
        max_length=16,
        choices=UserStatus.choices,
        default=UserStatus.PENDING,
        verbose_name=_("User Status"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Staff Status"))
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name=_("Date Joined"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(email__isnull=False) | Q(username__isnull=False) | Q(phone__isnull=False),
                name="user_requires_email_username_or_phone",
            ),
        ]

    def __str__(self):
        primary_contact = self.email or self.phone or str(self.id)
        return f"{self.name} ({primary_contact})"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
        if self.username:
            self.username = self.username.strip().lower()
        if not self.email and not self.username and not self.phone:
            raise ValidationError(_("Either email, username, or phone is required."))
        if self.role == UserRole.ADMIN:
            self.is_staff = True

    def save(self, *args, **kwargs):
        self.email = self.email or None
        self.username = self.username or None
        self.phone = self.phone or None
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.name

    @property
    def region(self):
        return self.location

    @property
    def is_adopter(self):
        return self.role == UserRole.ADOPTER

    @property
    def is_rescuer(self):
        return self.role == UserRole.RESCUER

    @property
    def is_admin_user(self):
        return self.role == UserRole.ADMIN

    def ensure_role_profile(self):
        if self.role == UserRole.ADOPTER:
            AdopterProfile.objects.get_or_create(user=self)
        elif self.role == UserRole.RESCUER:
            RescuerProfile.objects.get_or_create(user=self)

    def has_role_permission(self, resource, action):
        if self.is_superuser:
            return True
        if self.role != UserRole.ADMIN:
            return False

        admin_permission = AdminPermission.objects.filter(
            admin_profile__user=self,
            permission__module=resource,
        ).values_list("actions", flat=True).first()
        return action in (admin_permission or [])


class RescuerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="rescuer_profile")
    organization_name = models.CharField(max_length=150, blank=True, verbose_name=_("Organization Name"))
    experience_years = models.PositiveIntegerField(default=0, verbose_name=_("Experience Years"))
    verification_status = models.CharField(
        max_length=16,
        choices=RescuerVerificationStatus.choices,
        default=RescuerVerificationStatus.UNVERIFIED,
        verbose_name=_("Verification Status"),
    )
    successful_adoptions = models.PositiveIntegerField(default=0, verbose_name=_("Successful Adoptions"))
    response_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        verbose_name=_("Response Rate"),
        help_text=_("Stored as a percentage between 0 and 100."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Rescuer Profile")
        verbose_name_plural = _("Rescuer Profiles")

    def __str__(self):
        return self.organization_name or self.user.name

    def clean(self):
        super().clean()
        if self.user and self.user.role != UserRole.RESCUER:
            raise ValidationError(_("Rescuer profiles can only be assigned to rescuer users."))


class AdopterProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="adopter_profile")
    home_type = models.CharField(max_length=100, blank=True, verbose_name=_("Home Type"))
    pet_experience = models.TextField(blank=True, verbose_name=_("Pet Experience"))
    preferred_pet_type = models.CharField(max_length=100, blank=True, verbose_name=_("Preferred Pet Type"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Adopter Profile")
        verbose_name_plural = _("Adopter Profiles")

    def __str__(self):
        return self.user.name

    def clean(self):
        super().clean()
        if self.user and self.user.role != UserRole.ADOPTER:
            raise ValidationError(_("Adopter profiles can only be assigned to adopter users."))


class AdminProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")
    job_title = models.CharField(max_length=100, blank=True, verbose_name=_("Job Title"))
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_admins",
        verbose_name=_("Assigned By"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active Status"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Admin Profile")
        verbose_name_plural = _("Admin Profiles")

    def __str__(self):
        return f"{self.user.name} - {self.job_title or 'Admin'}"

    def clean(self):
        super().clean()
        if self.user and self.user.role != UserRole.ADMIN:
            raise ValidationError(_("Admin profiles can only be assigned to admin users."))


class InvitationStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REVOKED = "REVOKED", _("Revoked")
    EXPIRED = "EXPIRED", _("Expired")


class AdminInvitation(models.Model):
    TOKEN_SALT = "admin-invitation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name=_("Email Address"))
    job_title = models.CharField(max_length=100, blank=True, verbose_name=_("Job Title"))
    direct_permissions = models.JSONField(default=list, blank=True, verbose_name=_("Direct Permissions"))
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_invitations_sent",
        verbose_name=_("Invited By"),
    )
    expires_at = models.DateTimeField(verbose_name=_("Expires At"))
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Accepted At"))
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Revoked At"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Admin Invitation")
        verbose_name_plural = _("Admin Invitations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.email} - {self.status}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def status(self):
        if self.accepted_at:
            return InvitationStatus.ACCEPTED
        if self.revoked_at:
            return InvitationStatus.REVOKED
        if self.is_expired:
            return InvitationStatus.EXPIRED
        return InvitationStatus.PENDING

    @property
    def invitee_name(self):
        return self.email

    def issue_token(self):
        payload = {
            "invitation_id": str(self.id),
            "email": self.email,
            "expires_at": self.expires_at.isoformat(),
        }
        return signing.dumps(payload, salt=self.TOKEN_SALT)

    @classmethod
    def decode_token(cls, token):
        return signing.loads(token, salt=cls.TOKEN_SALT)


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.CharField(
        max_length=50,
        choices=AdminModule.choices,
        unique=True,
        verbose_name=_("Module"),
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = _("Permission")
        verbose_name_plural = _("Permissions")

    def __str__(self):
        return self.get_module_display()


class AdminPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_profile = models.ForeignKey(
        AdminProfile,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="admin_permissions",
        verbose_name=_("Permission"),
    )
    actions = models.JSONField(default=list, blank=True, verbose_name=_("Allowed Actions"))
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_permissions",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Admin Permission")
        verbose_name_plural = _("Admin Permissions")
        constraints = [
            models.UniqueConstraint(
                fields=["admin_profile", "permission"],
                name="unique_admin_permission",
            )
        ]
        indexes = [
            models.Index(fields=["admin_profile", "permission"]),
        ]

    def __str__(self):
        return f"{self.admin_profile.user.name} - {self.permission.module}:{','.join(self.actions)}"
