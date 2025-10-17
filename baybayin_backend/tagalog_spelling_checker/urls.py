from django.urls import path
from .views import check_spelling

urlpatterns = [
    path("check/", check_spelling, name="check_spelling"),
]