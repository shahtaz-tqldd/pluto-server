from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

v1_client_urls = [
    path("auth/", include("auth.api.v1.client.urls")),
    path("adopters/", include("adopters.api.v1.urls")),
    path("messages/", include("messages.api.v1.urls")),
    path("pets/", include("pets.api.v1.urls")),
    path("rescuers/", include("rescuers.api.v1.urls")),
]

v1_admin_urls = [
    path("auth/", include(("auth.api.v1.admin.urls"))),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
    path("api/v1/", include(v1_client_urls)),
    path("api/v1/admin/", include(v1_admin_urls)),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
