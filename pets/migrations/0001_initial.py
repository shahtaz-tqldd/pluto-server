import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Pet",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=150, verbose_name="Title")),
                ("species", models.CharField(choices=[("DOG", "Dog"), ("CAT", "Cat"), ("BIRD", "Bird"), ("RABBIT", "Rabbit"), ("OTHER", "Other")], max_length=20, verbose_name="Species")),
                ("breed", models.CharField(blank=True, max_length=100, verbose_name="Breed")),
                ("gender", models.CharField(choices=[("MALE", "Male"), ("FEMALE", "Female"), ("UNKNOWN", "Unknown")], default="UNKNOWN", max_length=16, verbose_name="Gender")),
                ("age_months", models.PositiveIntegerField(blank=True, help_text="Stored in months so pets can be filtered and sorted consistently.", null=True, verbose_name="Age In Months")),
                ("size", models.CharField(blank=True, choices=[("SMALL", "Small"), ("MEDIUM", "Medium"), ("LARGE", "Large"), ("EXTRA_LARGE", "Extra Large")], max_length=16, verbose_name="Size")),
                ("color", models.CharField(blank=True, max_length=100, verbose_name="Color")),
                ("vaccinated", models.BooleanField(default=False, verbose_name="Vaccinated")),
                ("sterilized", models.BooleanField(default=False, verbose_name="Sterilized")),
                ("medical_notes", models.TextField(blank=True, verbose_name="Medical Notes")),
                ("temperament", models.TextField(blank=True, verbose_name="Temperament")),
                ("story", models.TextField(blank=True, verbose_name="Story")),
                ("current_location", models.CharField(blank=True, max_length=150, verbose_name="Current Location")),
                ("rescue_location", models.CharField(blank=True, max_length=150, verbose_name="Rescue Location")),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("AVAILABLE", "Available"), ("PENDING", "Pending"), ("ADOPTED", "Adopted"), ("ON_HOLD", "On Hold"), ("ARCHIVED", "Archived")], default="DRAFT", max_length=16, verbose_name="Status")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                ("rescuer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pets", to=settings.AUTH_USER_MODEL, verbose_name="Rescuer")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PetImage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("image_url", models.URLField(verbose_name="Image URL")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Sort Order")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("pet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="pluto_pets.pet", verbose_name="Pet")),
            ],
            options={
                "ordering": ["sort_order", "created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="pet",
            index=models.Index(fields=["rescuer", "status"], name="pluto_pets__rescuer_4dfdbf_idx"),
        ),
        migrations.AddIndex(
            model_name="pet",
            index=models.Index(fields=["species", "status"], name="pluto_pets__species_38332b_idx"),
        ),
        migrations.AddIndex(
            model_name="petimage",
            index=models.Index(fields=["pet", "sort_order"], name="pluto_pets__pet_id_485ae0_idx"),
        ),
    ]
