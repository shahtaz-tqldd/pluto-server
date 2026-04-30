from django.urls import path

from pets.api.v1.views import PetDetailAPIView, PetFeedAPIView, PetListCreateAPIView, RescuerPetListAPIView


urlpatterns = [
    path("feed/", PetFeedAPIView.as_view(), name="pet-feed"),
    path("rescuer-pets/", RescuerPetListAPIView.as_view(), name="pet-my-pets"),
    path("", PetListCreateAPIView.as_view(), name="pet-list-create"),
    path("<uuid:id>/", PetDetailAPIView.as_view(), name="pet-detail"),
]
