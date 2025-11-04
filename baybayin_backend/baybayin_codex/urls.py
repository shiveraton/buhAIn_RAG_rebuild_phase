from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CodexCategoryViewSet, CodexArticleViewSet, CodexTimelineViewSet,
    CodexGlossaryViewSet, CodexQuizViewSet, CodexBookmarkViewSet, CodexStatsViewSet,
    CodexContentManagementViewSet, CodexSearchViewSet
)

router = DefaultRouter()
router.register(r'categories', CodexCategoryViewSet, basename='codex-categories')
router.register(r'articles', CodexArticleViewSet, basename='codex-articles')
router.register(r'timeline', CodexTimelineViewSet, basename='codex-timeline')
router.register(r'glossary', CodexGlossaryViewSet, basename='codex-glossary')
router.register(r'quiz', CodexQuizViewSet, basename='codex-quiz')
router.register(r'bookmarks', CodexBookmarkViewSet, basename='codex-bookmarks')
router.register(r'stats', CodexStatsViewSet, basename='codex-stats')
router.register(r'admin/content', CodexContentManagementViewSet, basename='codex-admin-content')
router.register(r'search', CodexSearchViewSet, basename='codex-search')

urlpatterns = [
    path('api/codex/', include(router.urls)),
    path('api/analyzer/', include('baybayin_codex.analyzer.urls')),
]
