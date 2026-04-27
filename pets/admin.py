from django.contrib import admin

from pets.models import Pet, PetImage


class PetImageInline(admin.TabularInline):
    model = PetImage
    extra = 0


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("title", "species", "status", "rescuer", "created_at")
    list_filter = ("species", "status", "gender", "vaccinated", "sterilized")
    search_fields = ("title", "breed", "color", "rescuer__name", "current_location")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [PetImageInline]


@admin.register(PetImage)
class PetImageAdmin(admin.ModelAdmin):
    list_display = ("pet", "sort_order", "created_at")
    search_fields = ("pet__title", "image_url")
    readonly_fields = ("id", "created_at")

