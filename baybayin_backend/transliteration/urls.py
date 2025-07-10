from django.urls import path
from .views import transliterate_text_view

urlpatterns = [
    path('api/transliterate/', transliterate_text_view, name="transliterate"),
    path('api/transliterate/text/', transliterate_text_view, name="transliterate_text"),  # Keep for backward compatibility
]