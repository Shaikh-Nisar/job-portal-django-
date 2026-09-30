from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", lambda request: redirect("login")),

    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),

    path("jobs/", include("jobs.urls")),

    path("api/", include("jobs.api_urls")),

    path("api/", include("applications.api_urls")),

    path("applications/", include("applications.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )