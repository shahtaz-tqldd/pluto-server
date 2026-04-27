from django.db.utils import OperationalError, ProgrammingError

from auth.models import AdminModule, Permission


def sync_default_permissions():
    for module, label in AdminModule.choices:
        Permission.objects.update_or_create(
            module=module,
            defaults={"description": f"Access to {label.lower()}."},
        )


def safe_sync_default_permissions(**kwargs):
    try:
        sync_default_permissions()
    except (OperationalError, ProgrammingError):
        # Tables may not exist yet during startup before migrations.
        return
