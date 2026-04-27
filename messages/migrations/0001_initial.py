import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pluto_pets", "0003_adoptionrequest_petmessage_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("ACTIVE", "Active"), ("CLOSED", "Closed")], default="ACTIVE", max_length=16, verbose_name="Status")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                ("adopter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_threads", to=settings.AUTH_USER_MODEL, verbose_name="Adopter")),
                ("adoption_request", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="message_thread", to="pluto_pets.adoptionrequest", verbose_name="Adoption Request")),
                ("pet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_threads", to="pluto_pets.pet", verbose_name="Pet")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body", models.TextField(verbose_name="Body")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="pluto_messages.conversation", verbose_name="Conversation")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_messages", to=settings.AUTH_USER_MODEL, verbose_name="Sender")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="conversation",
            index=models.Index(fields=["pet", "status"], name="pluto_messa_pet_id_19b620_idx"),
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.UniqueConstraint(fields=("pet", "adopter"), name="unique_message_conversation_per_adopter"),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["conversation", "created_at"], name="pluto_messa_convers_c86e51_idx"),
        ),
    ]
