from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WikiCategoryViewSet, WikiArticleViewSet, WikiTimelineViewSet,
    WikiGlossaryViewSet, WikiQuizViewSet, WikiBookmarkViewSet, WikiStatsViewSet,
    WikiContentManagementViewSet, WikiSearchViewSet
)
from  game_seg_trivia.views import TriviaQuestionView

router = DefaultRouter()
router.register(r'categories', WikiCategoryViewSet, basename='wiki-categories')
router.register(r'articles', WikiArticleViewSet, basename='wiki-articles')
router.register(r'timeline', WikiTimelineViewSet, basename='wiki-timeline')
router.register(r'glossary', WikiGlossaryViewSet, basename='wiki-glossary')
router.register(r'quiz', WikiQuizViewSet, basename='wiki-quiz')
router.register(r'bookmarks', WikiBookmarkViewSet, basename='wiki-bookmarks')
router.register(r'stats', WikiStatsViewSet, basename='wiki-stats')
router.register(r'admin/content', WikiContentManagementViewSet, basename='wiki-admin-content')
router.register(r'search', WikiSearchViewSet, basename='wiki-search')

urlpatterns = [
    path('api/wiki/', include(router.urls)),
    path('api/trivia/', TriviaQuestionView.as_view(), name='trivia-question'),
    path('api/analyzer/', include('baybayin_wiki.analyzer.urls')),
]
