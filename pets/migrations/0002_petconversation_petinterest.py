import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pluto_pets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PetInterest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                (
                    "pet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interests",
                        to="pluto_pets.pet",
                        verbose_name="Pet",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pet_interests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PetConversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "Active"), ("CLOSED", "Closed")],
                        default="ACTIVE",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "adopter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pet_conversations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Adopter",
                    ),
                ),
                (
                    "pet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversations",
                        to="pluto_pets.pet",
                        verbose_name="Pet",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="petinterest",
            index=models.Index(fields=["pet", "created_at"], name="pluto_pets__pet_id_5878bb_idx"),
        ),
        migrations.AddConstraint(
            model_name="petinterest",
            constraint=models.UniqueConstraint(fields=("pet", "user"), name="unique_pet_interest_per_user"),
        ),
        migrations.AddIndex(
            model_name="petconversation",
            index=models.Index(fields=["pet", "status"], name="pluto_pets__pet_id_9c0714_idx"),
        ),
        migrations.AddConstraint(
            model_name="petconversation",
            constraint=models.UniqueConstraint(fields=("pet", "adopter"), name="unique_pet_conversation_per_adopter"),
        ),
    ]
