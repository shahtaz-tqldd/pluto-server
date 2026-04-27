from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from app.utils.response import APIResponse
from messages.models import Conversation, ConversationStatus
from pets.models import AdoptionRequest, AdoptionRequestStatus, Pet, PetStatus
from rescuers.api.v1.serializers import (
    PublicRescuerProfileSerializer,
    RescuerAccountSerializer,
    RescuerAccountUpdateSerializer,
    RescuerAdoptionRequestSerializer,
    RescuerConversationSerializer,
    RescuerDashboardSerializer,
    RescuerReviewCreateSerializer,
    RescuerReviewSerializer,
)
from rescuers.models import RescuerReview
from rescuers.permissions import IsRescuer


User = get_user_model()


class RescuerProfileAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsRescuer]
    serializer_class = RescuerAccountUpdateSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        return APIResponse.success(
            data=RescuerAccountSerializer(request.user).data,
            message="Rescuer profile fetched successfully.",
        )

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return APIResponse.success(
            data=RescuerAccountSerializer(user).data,
            message="Rescuer profile updated successfully.",
        )


class RescuerDashboardAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsRescuer]

    def get(self, request, *args, **kwargs):
        payload = {
            "rescuer": request.user,
            "pets": Pet.objects.filter(rescuer=request.user).select_related("rescuer").prefetch_related("images"),
        }
        return APIResponse.success(
            data=RescuerDashboardSerializer(payload).data,
            message="Rescuer dashboard fetched successfully.",
        )


class RescuerAdoptionRequestInboxAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsRescuer]

    def get(self, request, *args, **kwargs):
        queryset = (
            AdoptionRequest.objects.filter(pet__rescuer=request.user)
            .select_related("pet", "adopter")
            .prefetch_related("pet__images")
            .order_by("-created_at")
        )
        return APIResponse.success(
            data=RescuerAdoptionRequestSerializer(queryset, many=True).data,
            message="Adoption request inbox fetched successfully.",
        )


class RescuerAdoptionRequestActionAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsRescuer]

    def post(self, request, request_id, action, *args, **kwargs):
        adoption_request = get_object_or_404(
            AdoptionRequest.objects.select_related("pet", "adopter", "pet__rescuer"),
            id=request_id,
            pet__rescuer=request.user,
        )

        if action == "accept":
            if adoption_request.status != AdoptionRequestStatus.PENDING:
                return APIResponse.error(message="Only pending requests can be accepted.", status=status.HTTP_400_BAD_REQUEST)

            adoption_request.status = AdoptionRequestStatus.ACCEPTED
            adoption_request.accepted_at = timezone.now()
            adoption_request.rejected_at = None
            adoption_request.save(update_fields=["status", "accepted_at", "rejected_at", "updated_at"])

            conversation, _ = Conversation.objects.get_or_create(
                pet=adoption_request.pet,
                adopter=adoption_request.adopter,
                defaults={
                    "status": ConversationStatus.ACTIVE,
                    "adoption_request": adoption_request,
                },
            )
            if conversation.adoption_request_id != adoption_request.id or conversation.status != ConversationStatus.ACTIVE:
                conversation.adoption_request = adoption_request
                conversation.status = ConversationStatus.ACTIVE
                conversation.save(update_fields=["adoption_request", "status", "updated_at"])

            adoption_request.pet.status = PetStatus.PENDING
            adoption_request.pet.save(update_fields=["status", "updated_at"])
            return APIResponse.success(
                data={
                    "request": RescuerAdoptionRequestSerializer(adoption_request).data,
                    "conversation": RescuerConversationSerializer(conversation).data,
                },
                message="Adoption request accepted successfully.",
            )

        if action == "reject":
            if adoption_request.status != AdoptionRequestStatus.PENDING:
                return APIResponse.error(message="Only pending requests can be rejected.", status=status.HTTP_400_BAD_REQUEST)
            adoption_request.status = AdoptionRequestStatus.REJECTED
            adoption_request.rejected_at = timezone.now()
            adoption_request.save(update_fields=["status", "rejected_at", "updated_at"])
            return APIResponse.success(
                data=RescuerAdoptionRequestSerializer(adoption_request).data,
                message="Adoption request rejected successfully.",
            )

        return APIResponse.error(message="Invalid action.", status=status.HTTP_400_BAD_REQUEST)


class RescuerConversationListAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsRescuer]

    def get(self, request, *args, **kwargs):
        queryset = (
            Conversation.objects.filter(pet__rescuer=request.user)
            .select_related("pet", "pet__rescuer", "adopter", "adoption_request")
            .prefetch_related("pet__images", "messages")
            .order_by("-updated_at")
        )
        return APIResponse.success(
            data=RescuerConversationSerializer(queryset, many=True).data,
            message="Rescuer conversations fetched successfully.",
        )


class RescuerMarkPetAdoptedAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsRescuer]

    def post(self, request, pet_id, *args, **kwargs):
        pet = get_object_or_404(Pet, id=pet_id, rescuer=request.user)
        pet.status = PetStatus.ADOPTED
        pet.save(update_fields=["status", "updated_at"])

        Conversation.objects.filter(pet=pet).update(status=ConversationStatus.CLOSED)
        AdoptionRequest.objects.filter(pet=pet, status=AdoptionRequestStatus.PENDING).update(
            status=AdoptionRequestStatus.REJECTED,
            rejected_at=timezone.now(),
            updated_at=timezone.now(),
        )
        return APIResponse.success(message="Pet marked as adopted successfully.")


class PublicRescuerProfileAPIView(GenericAPIView):
    def get(self, request, rescuer_id, *args, **kwargs):
        rescuer = get_object_or_404(
            User.objects.select_related("rescuer_profile")
            .annotate(
                review_count=Count("received_rescuer_reviews", distinct=True),
                average_rating=Avg("received_rescuer_reviews__rating"),
            ),
            id=rescuer_id,
            role="RESCUER",
        )
        pet_queryset = (
            Pet.objects.filter(rescuer=rescuer)
            .prefetch_related(Prefetch("images"))
            .annotate(
                interested_count=Count("interests", distinct=True),
                active_conversation_count=Count(
                    "message_threads",
                    filter=Q(message_threads__status="ACTIVE"),
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )
        reviews = (
            RescuerReview.objects.filter(rescuer=rescuer)
            .select_related("author")
            .order_by("-created_at")
        )
        payload = {
            "rescuer": rescuer,
            "rescued_pet_list": pet_queryset,
            "current_available_pets": list(pet_queryset.filter(status=PetStatus.AVAILABLE)),
            "adopted_pet_history": list(pet_queryset.filter(status=PetStatus.ADOPTED)),
            "reviews": reviews,
            "trust_indicators": {
                "review_count": rescuer.review_count or 0,
                "average_rating": round(float(rescuer.average_rating or 0), 2),
                "total_rescued_pets": pet_queryset.count(),
                "current_available_pets": pet_queryset.filter(status=PetStatus.AVAILABLE).count(),
                "adopted_pet_count": pet_queryset.filter(status=PetStatus.ADOPTED).count(),
                "is_verified": rescuer.is_verified,
                "verification_status": getattr(getattr(rescuer, "rescuer_profile", None), "verification_status", ""),
            },
        }
        return APIResponse.success(
            data=PublicRescuerProfileSerializer(payload).data,
            message="Public rescuer profile fetched successfully.",
        )


class RescuerReviewListCreateAPIView(GenericAPIView):
    def get(self, request, rescuer_id, *args, **kwargs):
        get_object_or_404(User.objects.all(), id=rescuer_id, role="RESCUER")
        queryset = (
            RescuerReview.objects.filter(rescuer_id=rescuer_id, rescuer__role="RESCUER")
            .select_related("author")
            .order_by("-created_at")
        )
        return APIResponse.success(
            data=RescuerReviewSerializer(queryset, many=True).data,
            message="Rescuer reviews fetched successfully.",
        )

    permission_classes = []

    def post(self, request, rescuer_id, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return APIResponse.error(message="Authentication required.", status=status.HTTP_401_UNAUTHORIZED)

        rescuer = get_object_or_404(
            User.objects.select_related("rescuer_profile"),
            id=rescuer_id,
            role="RESCUER",
        )
        serializer = RescuerReviewCreateSerializer(
            data=request.data,
            context={"request": request, "rescuer": rescuer},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return APIResponse.success(
            data=RescuerReviewSerializer(review).data,
            message="Rescuer review submitted successfully.",
            status=status.HTTP_201_CREATED,
        )
