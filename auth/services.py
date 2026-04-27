from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils import timezone

from auth.models import AdminInvitation, AdminPermission, AdminProfile, Permission, UserRole
from auth.tasks import send_admin_invitation_email


def build_admin_invitation_url(token):
    query = urlencode({"token": token})
    return f"{settings.ADMIN_FRONTEND_URL.rstrip('/')}{settings.ADMIN_INVITATION_PATH}?{query}"


def send_admin_invitation(invitation):
    token = invitation.issue_token()
    registration_url = build_admin_invitation_url(token)

    subject = "You have been invited to join pluto admin"
    recipient_name = invitation.invitee_name or invitation.email
    inviter_name = (
        invitation.invited_by.full_name
        if invitation.invited_by and invitation.invited_by.full_name
        else invitation.invited_by.email
        if invitation.invited_by
        else "pluto"
    )
    expires_at = timezone.localtime(invitation.expires_at).strftime("%Y-%m-%d %H:%M:%S %Z")
    permissions = [
        {
            "module": item["module"].replace("_", " ").title(),
            "actions": ", ".join(action.title() for action in item["actions"]),
        }
        for item in invitation.direct_permissions
    ]
    context = {
        "recipient_name": recipient_name,
        "inviter_name": inviter_name,
        "job_title": invitation.job_title,
        "expires_at": expires_at,
        "registration_url": registration_url,
        "permissions": permissions,
    }
    message = render_to_string("auth/emails/admin_invitation.txt", context)
    html_message = render_to_string("auth/emails/admin_invitation.html", context)

    try:
        send_admin_invitation_email.delay(
            recipient_email=invitation.email,
            subject=subject,
            message=message,
            html_message=html_message,
        )
    except Exception:
        send_admin_invitation_email(
            recipient_email=invitation.email,
            subject=subject,
            message=message,
            html_message=html_message,
        )

    return {"token": token, "registration_url": registration_url}


def assign_admin_access(user, permissions, assigned_by=None, job_title=""):
    if user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        user.is_staff = True
        user.save(update_fields=["role", "is_staff", "updated_at"])

    admin_profile, _ = AdminProfile.objects.update_or_create(
        user=user,
        defaults={
            "job_title": job_title,
            "assigned_by": assigned_by,
            "is_active": True,
        },
    )

    modules = [item["module"] for item in permissions]
    if modules:
        AdminPermission.objects.filter(admin_profile=admin_profile).exclude(
            permission__module__in=modules
        ).delete()
    else:
        AdminPermission.objects.filter(admin_profile=admin_profile).delete()

    for item in permissions:
        permission, _ = Permission.objects.get_or_create(
            module=item["module"],
            defaults={"description": f"Access to {item['module'].replace('_', ' ').lower()}."},
        )
        actions = list(dict.fromkeys(item["actions"]))
        AdminPermission.objects.update_or_create(
            admin_profile=admin_profile,
            permission=permission,
            defaults={"actions": actions, "granted_by": assigned_by},
        )

    return admin_profile


def resolve_admin_invitation(token):
    try:
        payload = AdminInvitation.decode_token(token)
    except Exception as exc:
        raise ValidationError("Invitation token is invalid.") from exc

    invitation = (
        AdminInvitation.objects.select_related("invited_by")
        .filter(id=payload.get("invitation_id"), email=payload.get("email"))
        .first()
    )
    if invitation is None:
        raise ValidationError("Invitation does not exist.")

    expires_at = payload.get("expires_at")
    if expires_at != invitation.expires_at.isoformat():
        raise ValidationError("Invitation token is no longer valid.")

    if invitation.revoked_at:
        raise ValidationError("Invitation has been revoked.")
    if invitation.accepted_at:
        raise ValidationError("Invitation has already been used.")
    if invitation.is_expired:
        raise ValidationError("Invitation has expired.")

    return invitation
