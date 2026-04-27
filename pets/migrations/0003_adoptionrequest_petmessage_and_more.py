import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pluto_pets", "0002_petconversation_petinterest"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdoptionRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("intention", models.CharField(max_length=255, verbose_name="Adoption Intention")),
                ("message", models.TextField(blank=True, verbose_name="Message")),
                (
                    "status",
                    models.CharField(
                        choices=[("PENDING", "Pending"), ("ACCEPTED", "Accepted"), ("REJECTED", "Rejected"), ("WITHDRAWN", "Withdrawn")],
                        default="PENDING",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                ("accepted_at", models.DateTimeField(blank=True, null=True, verbose_name="Accepted At")),
                ("rejected_at", models.DateTimeField(blank=True, null=True, verbose_name="Rejected At")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "adopter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adoption_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Adopter",
                    ),
                ),
                (
                    "pet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adoption_requests",
                        to="pluto_pets.pet",
                        verbose_name="Pet",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PetMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body", models.TextField(verbose_name="Body")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="pluto_pets.petconversation",
                        verbose_name="Conversation",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pet_messages",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Sender",
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddField(
            model_name="petconversation",
            name="adoption_request",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="conversation",
                to="pluto_pets.adoptionrequest",
                verbose_name="Adoption Request",
            ),
        ),
        migrations.AddIndex(
            model_name="adoptionrequest",
            index=models.Index(fields=["pet", "status"], name="pluto_pets__pet_id_a5c8b4_idx"),
        ),
        migrations.AddIndex(
            model_name="adoptionrequest",
            index=models.Index(fields=["adopter", "status"], name="pluto_pets__adopter_15765c_idx"),
        ),
        migrations.AddConstraint(
            model_name="adoptionrequest",
            constraint=models.UniqueConstraint(
                condition=models.Q(status__in=["PENDING", "ACCEPTED"]),
                fields=("pet", "adopter"),
                name="unique_open_adoption_request_per_pet_adopter",
            ),
        ),
        migrations.AddIndex(
            model_name="petmessage",
            index=models.Index(fields=["conversation", "created_at"], name="pluto_pets__convers_72d78b_idx"),
        ),
    ]
