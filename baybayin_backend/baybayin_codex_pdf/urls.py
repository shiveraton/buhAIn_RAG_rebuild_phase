from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PDFCodexViewSet

router = DefaultRouter()
router.register(r'articles', PDFCodexViewSet, basename='pdf-codex')

urlpatterns = [
    path('api/codex/', include(router.urls)),
]
