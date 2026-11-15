from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health),
    path("items", views.create_item),
]
