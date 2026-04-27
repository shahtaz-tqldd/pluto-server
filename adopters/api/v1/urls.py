from django.urls import path

from adopters.api.v1.views import (
    AdopterAdoptionRequestListCreateAPIView,
    AdopterConversationListAPIView,
    AdopterReviewListCreateAPIView,
    AdopterProfileAPIView,
    PublicAdopterProfileAPIView,
)


urlpatterns = [
    path("me/", AdopterProfileAPIView.as_view(), name="adopter-profile"),
    path("adoption-requests/", AdopterAdoptionRequestListCreateAPIView.as_view(), name="adopter-adoption-request-list"),
    path("conversations/", AdopterConversationListAPIView.as_view(), name="adopter-conversation-list"),
    path("public/<uuid:adopter_id>/", PublicAdopterProfileAPIView.as_view(), name="adopter-public-profile"),
    path("public/<uuid:adopter_id>/reviews/", AdopterReviewListCreateAPIView.as_view(), name="adopter-review-list-create"),
    path(
        "pets/<uuid:pet_id>/adoption-request/",
        AdopterAdoptionRequestListCreateAPIView.as_view(),
        name="adopter-adoption-request-create",
    ),
]
