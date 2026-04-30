from django.db.models import Count, Prefetch, Q
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from app.base.pagination import CustomPagination
from app.utils.response import APIResponse
from pets.models import Pet, PetStatus
from pets.permissions import IsPetOwnerOrAdmin, IsRescuer
from pets.api.v1.serializers import PetFeedSerializer, PetSerializer, PetWriteSerializer


class PetListCreateAPIView(GenericAPIView):
    queryset = Pet.objects.select_related("rescuer").prefetch_related("images").all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsRescuer()]
        return []

    def get(self, request, *args, **kwargs):
        pets = self.get_queryset()
        serializer = PetSerializer(pets, many=True)
        return APIResponse.success(data=serializer.data, message="Pets fetched successfully.")

    def post(self, request, *args, **kwargs):
        serializer = PetWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        pet = serializer.save()
        return APIResponse.success(
            data=PetSerializer(pet).data,
            message="Pet listed successfully.",
            status=status.HTTP_201_CREATED,
        )


class RescuerPetListAPIView(GenericAPIView):
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, IsRescuer]

    def get_queryset(self):
        queryset = (
            Pet.objects.select_related("rescuer")
            .prefetch_related(Prefetch("images"))
            .filter(rescuer=self.request.user)
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

        status_param = self.request.query_params.get("status", "").strip().lower()
        if status_param:
            allowed_statuses = {
                "available": PetStatus.AVAILABLE,
                "adopted": PetStatus.ADOPTED,
            }
            queryset = queryset.filter(status=allowed_statuses[status_param])

        return queryset

    def get(self, request, *args, **kwargs):
        status_param = request.query_params.get("status", "").strip().lower()
        if status_param and status_param not in {"available", "adopted"}:
            return APIResponse.error(
                message="Invalid status filter. Use available or adopted.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PetSerializer(page, many=True)
        return APIResponse.success(
            data=serializer.data,
            meta={
                "page": paginator.page.number,
                "page_size": paginator.get_page_size(request),
                "total_pages": paginator.page.paginator.num_pages,
                "total_items": paginator.page.paginator.count,
            },
            message="My pets fetched successfully.",
        )


class PetFeedAPIView(GenericAPIView):
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = (
            Pet.objects.select_related("rescuer")
            .prefetch_related(Prefetch("images"))
            .annotate(
                interested_count=Count("interests", distinct=True),
                active_conversation_count=Count(
                    "message_threads",
                    filter=Q(message_threads__status="ACTIVE"),
                    distinct=True,
                ),
            )
        )

        params = self.request.query_params
        keyword = params.get("search", "").strip()
        species = params.get("species", "").strip()
        breed = params.get("breed", "").strip()
        location = params.get("location", "").strip()
        available_only = params.get("available_only", "true").strip().lower()
        nearby = params.get("nearby", "").strip().lower()
        sort = params.get("sort", "latest").strip().lower()

        if available_only not in {"0", "false", "no", "off"}:
            queryset = queryset.filter(status="AVAILABLE")

        if species:
            queryset = queryset.filter(species__iexact=species)
        if breed:
            queryset = queryset.filter(breed__icontains=breed)
        if location:
            queryset = queryset.filter(current_location__icontains=location)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(species__icontains=keyword)
                | Q(breed__icontains=keyword)
                | Q(current_location__icontains=keyword)
                | Q(story__icontains=keyword)
                | Q(temperament__icontains=keyword)
            )

        if nearby in {"1", "true", "yes", "on"} and self.request.user.is_authenticated:
            user_location = (getattr(self.request.user, "location", "") or "").strip()
            if user_location:
                queryset = queryset.filter(current_location__icontains=user_location)

        if sort == "latest":
            queryset = queryset.order_by("-created_at")
        elif sort == "oldest":
            queryset = queryset.order_by("created_at")
        elif sort == "most_interested":
            queryset = queryset.order_by("-interested_count", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PetFeedSerializer(page, many=True)
        return APIResponse.success(
            data=serializer.data,
            meta={
                "page": paginator.page.number,
                "page_size": paginator.get_page_size(request),
                "total_pages": paginator.page.paginator.num_pages,
                "total_items": paginator.page.paginator.count,
            },
            message="Pet feed fetched successfully.",
        )


class PetDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = (
        Pet.objects.select_related("rescuer")
        .prefetch_related("images")
        .annotate(
            interested_count=Count("interests", distinct=True),
            active_conversation_count=Count(
                "message_threads",
                filter=Q(message_threads__status="ACTIVE"),
                distinct=True,
            ),
        )
    )
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method in {"PATCH", "DELETE"}:
            return [IsAuthenticated(), IsPetOwnerOrAdmin()]
        return []

    def get_serializer_class(self):
        if self.request.method in {"PATCH", "PUT"}:
            return PetWriteSerializer
        return PetSerializer

    def retrieve(self, request, *args, **kwargs):
        pet = self.get_object()
        return APIResponse.success(data=PetSerializer(pet).data, message="Pet fetched successfully.")

    def patch(self, request, *args, **kwargs):
        pet = self.get_object()
        self.check_object_permissions(request, pet)
        serializer = PetWriteSerializer(pet, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        pet = serializer.save()
        return APIResponse.success(data=PetSerializer(pet).data, message="Pet updated successfully.")

    def delete(self, request, *args, **kwargs):
        pet = self.get_object()
        self.check_object_permissions(request, pet)
        pet.delete()
        return APIResponse.success(message="Pet deleted successfully.")
