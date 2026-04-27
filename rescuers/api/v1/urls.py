from django.urls import path

from rescuers.api.v1.views import (
    PublicRescuerProfileAPIView,
    RescuerAdoptionRequestActionAPIView,
    RescuerAdoptionRequestInboxAPIView,
    RescuerConversationListAPIView,
    RescuerDashboardAPIView,
    RescuerMarkPetAdoptedAPIView,
    RescuerProfileAPIView,
    RescuerReviewListCreateAPIView,
)


urlpatterns = [
    path("me/", RescuerProfileAPIView.as_view(), name="rescuer-profile"),
    path("dashboard/", RescuerDashboardAPIView.as_view(), name="rescuer-dashboard"),
    path("public/<uuid:rescuer_id>/", PublicRescuerProfileAPIView.as_view(), name="rescuer-public-profile"),
    path("public/<uuid:rescuer_id>/reviews/", RescuerReviewListCreateAPIView.as_view(), name="rescuer-review-list-create"),
    path("adoption-requests/", RescuerAdoptionRequestInboxAPIView.as_view(), name="rescuer-adoption-request-inbox"),
    path(
        "adoption-requests/<uuid:request_id>/<str:action>/",
        RescuerAdoptionRequestActionAPIView.as_view(),
        name="rescuer-adoption-request-action",
    ),
    path("conversations/", RescuerConversationListAPIView.as_view(), name="rescuer-conversation-list"),
    path("pets/<uuid:pet_id>/mark-adopted/", RescuerMarkPetAdoptedAPIView.as_view(), name="rescuer-pet-mark-adopted"),
]
