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
            name="AdopterReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rating", models.PositiveSmallIntegerField(verbose_name="Rating")),
                ("message", models.TextField(blank=True, verbose_name="Message")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "adopter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_adopter_reviews",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Adopter",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="written_adopter_reviews",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Author",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="adopterreview",
            index=models.Index(fields=["adopter", "created_at"], name="pluto_adopt_adopter_f1f186_idx"),
        ),
        migrations.AddConstraint(
            model_name="adopterreview",
            constraint=models.UniqueConstraint(fields=("adopter", "author"), name="unique_adopter_review_per_author"),
        ),
        migrations.AddConstraint(
            model_name="adopterreview",
            constraint=models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="adopter_review_rating_between_1_and_5",
            ),
        ),
    ]
