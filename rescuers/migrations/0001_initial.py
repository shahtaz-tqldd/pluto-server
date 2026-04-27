import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RescuerReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rating", models.PositiveSmallIntegerField(verbose_name="Rating")),
                ("message", models.TextField(blank=True, verbose_name="Message")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="written_rescuer_reviews",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Author",
                    ),
                ),
                (
                    "rescuer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_rescuer_reviews",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Rescuer",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="rescuerreview",
            index=models.Index(fields=["rescuer", "created_at"], name="pluto_rescu_rescuer_9270b5_idx"),
        ),
        migrations.AddConstraint(
            model_name="rescuerreview",
            constraint=models.UniqueConstraint(fields=("rescuer", "author"), name="unique_rescuer_review_per_author"),
        ),
        migrations.AddConstraint(
            model_name="rescuerreview",
            constraint=models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="rescuer_review_rating_between_1_and_5",
            ),
        ),
    ]
