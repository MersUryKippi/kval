from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.record_list, name="list"),
    path("add/", views.record_create, name="add"),
    path("<int:pk>/edit/", views.record_edit, name="edit"),
    path("<int:pk>/remove/", views.record_delete, name="remove"),
]
