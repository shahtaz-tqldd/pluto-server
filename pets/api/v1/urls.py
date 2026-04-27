from django.urls import path

from pets.api.v1.views import PetDetailAPIView, PetFeedAPIView, PetListCreateAPIView


urlpatterns = [
    path("feed/", PetFeedAPIView.as_view(), name="pet-feed"),
    path("", PetListCreateAPIView.as_view(), name="pet-list-create"),
    path("<uuid:id>/", PetDetailAPIView.as_view(), name="pet-detail"),
]
