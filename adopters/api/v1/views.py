from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from adopters.api.v1.serializers import (
    AdopterAccountSerializer,
    AdopterAccountUpdateSerializer,
    AdopterConversationSerializer,
    AdopterAdoptionRequestCreateSerializer,
    AdopterAdoptionRequestSerializer,
    AdopterReviewCreateSerializer,
    AdopterReviewSerializer,
    PublicAdopterProfileSerializer,
)
from adopters.models import AdopterReview
from adopters.permissions import IsAdopter
from app.utils.response import APIResponse
from messages.models import Conversation
from pets.models import AdoptionRequest, AdoptionRequestStatus, Pet, PetStatus


User = get_user_model()


class AdopterProfileAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdopter]
    serializer_class = AdopterAccountUpdateSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        return APIResponse.success(
            data=AdopterAccountSerializer(request.user).data,
            message="Adopter profile fetched successfully.",
        )

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return APIResponse.success(
            data=AdopterAccountSerializer(user).data,
            message="Adopter profile updated successfully.",
        )


class AdopterAdoptionRequestListCreateAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdopter]

    def get(self, request, *args, **kwargs):
        queryset = (
            AdoptionRequest.objects.filter(adopter=request.user)
            .select_related("pet", "adopter")
            .prefetch_related("pet__images")
            .order_by("-created_at")
        )
        return APIResponse.success(
            data=AdopterAdoptionRequestSerializer(queryset, many=True).data,
            message="Adoption requests fetched successfully.",
        )

    def post(self, request, pet_id, *args, **kwargs):
        pet = get_object_or_404(Pet.objects.select_related("rescuer").prefetch_related("images"), id=pet_id)
        serializer = AdopterAdoptionRequestCreateSerializer(
            data=request.data,
            context={"request": request, "pet": pet},
        )
        serializer.is_valid(raise_exception=True)
        adoption_request = serializer.save()
        return APIResponse.success(
            data=AdopterAdoptionRequestSerializer(adoption_request).data,
            message="Adoption request sent successfully.",
            status=status.HTTP_201_CREATED,
        )


class AdopterConversationListAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdopter]

    def get(self, request, *args, **kwargs):
        queryset = (
            Conversation.objects.filter(adopter=request.user)
            .select_related("pet", "pet__rescuer", "adopter", "adoption_request")
            .prefetch_related("pet__images", "messages")
            .order_by("-updated_at")
        )
        return APIResponse.success(
            data=AdopterConversationSerializer(queryset, many=True).data,
            message="Adopter conversations fetched successfully.",
        )


class PublicAdopterProfileAPIView(GenericAPIView):
    def get(self, request, adopter_id, *args, **kwargs):
        adopter = get_object_or_404(
            User.objects.select_related("adopter_profile")
            .annotate(
                review_count=Count("received_adopter_reviews", distinct=True),
                average_rating=Avg("received_adopter_reviews__rating"),
            ),
            id=adopter_id,
            role="ADOPTER",
        )
        adoption_activity = (
            AdoptionRequest.objects.filter(adopter=adopter)
            .select_related("pet", "adopter")
            .prefetch_related("pet__images")
            .order_by("-created_at")
        )
        adopted_pet_history = (
            Pet.objects.filter(
                adoption_requests__adopter=adopter,
                adoption_requests__status=AdoptionRequestStatus.ACCEPTED,
                status=PetStatus.ADOPTED,
            )
            .prefetch_related(Prefetch("images"))
            .annotate(
                interested_count=Count("interests", distinct=True),
                active_conversation_count=Count(
                    "message_threads",
                    filter=Q(message_threads__status="ACTIVE"),
                    distinct=True,
                ),
            )
            .distinct()
            .order_by("-updated_at")
        )
        reviews = (
            AdopterReview.objects.filter(adopter=adopter)
            .select_related("author")
            .order_by("-created_at")
        )
        payload = {
            "adopter": adopter,
            "adoption_activity": adoption_activity,
            "adopted_pet_history": adopted_pet_history,
            "reviews": reviews,
            "trust_indicators": {
                "review_count": adopter.review_count or 0,
                "average_rating": round(float(adopter.average_rating or 0), 2),
                "total_requests": adoption_activity.count(),
                "accepted_requests": adoption_activity.filter(status=AdoptionRequestStatus.ACCEPTED).count(),
                "adopted_pet_count": adopted_pet_history.count(),
                "is_verified": adopter.is_verified,
            },
        }
        return APIResponse.success(
            data=PublicAdopterProfileSerializer(payload).data,
            message="Public adopter profile fetched successfully.",
        )


class AdopterReviewListCreateAPIView(GenericAPIView):
    permission_classes = []

    def get(self, request, adopter_id, *args, **kwargs):
        get_object_or_404(User.objects.all(), id=adopter_id, role="ADOPTER")
        queryset = (
            AdopterReview.objects.filter(adopter_id=adopter_id, adopter__role="ADOPTER")
            .select_related("author")
            .order_by("-created_at")
        )
        return APIResponse.success(
            data=AdopterReviewSerializer(queryset, many=True).data,
            message="Adopter reviews fetched successfully.",
        )

    def post(self, request, adopter_id, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return APIResponse.error(message="Authentication required.", status=status.HTTP_401_UNAUTHORIZED)

        adopter = get_object_or_404(
            User.objects.select_related("adopter_profile"),
            id=adopter_id,
            role="ADOPTER",
        )
        serializer = AdopterReviewCreateSerializer(
            data=request.data,
            context={"request": request, "adopter": adopter},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return APIResponse.success(
            data=AdopterReviewSerializer(review).data,
            message="Adopter review submitted successfully.",
            status=status.HTTP_201_CREATED,
        )
