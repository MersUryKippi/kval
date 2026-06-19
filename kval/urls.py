from django.contrib import admin
from django.urls import include, path

from main.views import healthcheck

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ping/", healthcheck, name="ping"),
    path("", include("main.urls")),
]
