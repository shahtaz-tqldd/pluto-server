import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth.models import UserRole


class AdopterReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    adopter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_adopter_reviews",
        verbose_name=_("Adopter"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="written_adopter_reviews",
        verbose_name=_("Author"),
    )
    rating = models.PositiveSmallIntegerField(verbose_name=_("Rating"))
    message = models.TextField(blank=True, verbose_name=_("Message"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["adopter", "author"], name="unique_adopter_review_per_author"),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="adopter_review_rating_between_1_and_5",
            ),
        ]
        indexes = [
            models.Index(fields=["adopter", "created_at"]),
        ]

    def __str__(self):
        return f"{self.author_id} review for {self.adopter_id}"

    def clean(self):
        super().clean()
        if self.adopter_id == self.author_id:
            raise ValidationError({"author": _("You cannot review yourself.")})
        if self.adopter and self.adopter.role != UserRole.ADOPTER:
            raise ValidationError({"adopter": _("Reviews can only be attached to adopter users.")})
        if self.author and self.author.role not in {UserRole.RESCUER, UserRole.ADMIN}:
            raise ValidationError({"author": _("Only rescuers or admins can leave adopter reviews.")})
