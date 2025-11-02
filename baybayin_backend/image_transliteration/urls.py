from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import transliterate_image_view

urlpatterns = [
    path('api/transliterate/image/', transliterate_image_view, name="transliterate_image"),
]