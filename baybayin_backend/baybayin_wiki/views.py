from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import (
    WikiCategory, WikiArticle, WikiTimeline, WikiGlossary, 
    WikiQuiz, WikiBookmark, WikiReadingProgress
)
from .serializers import (
    WikiCategorySerializer, WikiArticleListSerializer, WikiArticleDetailSerializer,
    WikiTimelineSerializer, WikiGlossarySerializer, WikiQuizSerializer,
    WikiBookmarkSerializer, WikiReadingProgressSerializer
)
from .services import WikiContentService
import logging

logger = logging.getLogger(__name__)


class WikiCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for wiki categories with article counts
    """
    serializer_class = WikiCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'article_count']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        # Use the model field, not annotation to avoid conflicts
        return WikiCategory.objects.all()


class WikiArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for wiki articles with list and detail views
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty_level', 'is_featured']
    search_fields = ['title', 'content', 'summary', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'reading_time']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return WikiArticle.objects.filter(is_published=True).select_related('category')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WikiArticleDetailSerializer
        return WikiArticleListSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Toggle bookmark for an article"""
        article = self.get_object()
        bookmark, created = WikiBookmark.objects.get_or_create(
            user=request.user, 
            article=article
        )
        
        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})
        
        return Response({'bookmarked': True})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_progress(self, request, pk=None):
        """Update reading progress for an article"""
        article = self.get_object()
        percentage = request.data.get('percentage', 0)
        
        progress, created = WikiReadingProgress.objects.get_or_create(
            user=request.user,
            article=article,
            defaults={'progress_percentage': percentage}
        )
        
        if not created:
            progress.progress_percentage = percentage
            progress.completed = percentage >= 100
            progress.save()
        
        serializer = WikiReadingProgressSerializer(progress)
        return Response(serializer.data)


class WikiTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for historical timeline events
    """
    queryset = WikiTimeline.objects.all()
    serializer_class = WikiTimelineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['year', 'importance', 'period']
    search_fields = ['title', 'description']
    ordering_fields = ['year', 'importance', 'created_at']
    ordering = ['year']


class WikiGlossaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for glossary terms
    """
    queryset = WikiGlossary.objects.all()
    serializer_class = WikiGlossarySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty_level']
    search_fields = ['term', 'definition', 'pronunciation']
    ordering_fields = ['term', 'created_at']
    ordering = ['term']


class WikiQuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for quiz questions
    """
    queryset = WikiQuiz.objects.select_related('article').all()
    serializer_class = WikiQuizSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['article', 'difficulty']
    search_fields = ['question', 'explanation']
    ordering_fields = ['created_at', 'difficulty']
    ordering = ['created_at']


class WikiBookmarkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user bookmarks
    """
    serializer_class = WikiBookmarkSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['article__category']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return WikiBookmark.objects.filter(user=self.request.user).select_related('article')


class WikiReadingProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading progress
    """
    serializer_class = WikiReadingProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['completed', 'article__category']
    ordering_fields = ['last_read_at', 'progress_percentage']
    ordering = ['-last_read_at']
    
    def get_queryset(self):
        return WikiReadingProgress.objects.filter(user=self.request.user).select_related('article')


class WikiStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for wiki statistics
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get wiki overview statistics"""
        stats = {
            'total_articles': WikiArticle.objects.filter(is_published=True).count(),
            'total_categories': WikiCategory.objects.count(),
            'total_timeline_events': WikiTimeline.objects.count(),
            'total_glossary_terms': WikiGlossary.objects.count(),
            'featured_articles': WikiArticle.objects.filter(is_featured=True, is_published=True).count(),
        }
        
        if request.user.is_authenticated:
            stats.update({
                'bookmarked_articles': WikiBookmark.objects.filter(user=request.user).count(),
                'completed_articles': WikiReadingProgress.objects.filter(
                    user=request.user, completed=True
                ).count(),
            })
        
        return Response(stats)


class WikiContentManagementViewSet(viewsets.ViewSet):
    """
    Admin ViewSet for managing wiki content scraping and updates
    """
    permission_classes = [IsAdminUser]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wiki_service = WikiContentService()

    @action(detail=False, methods=['post'])
    def scrape_content(self, request):
        """Trigger content scraping from all sources"""
        try:
            force_refresh = request.data.get('force_refresh', False)
            logger.info(f"Content scraping triggered by admin. Force refresh: {force_refresh}")
            
            result = self.wiki_service.scrape_and_update_content(force_refresh=force_refresh)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Content scraping completed successfully',
                    'data': {
                        'scraping_completed_at': result.get('scraping_completed_at'),
                        'quality_report': result.get('quality_report', {}),
                        'save_stats': result.get('save_result', {}).get('stats', {}),
                        'content_stats': result.get('content_stats', {})
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': f"Content scraping failed: {result.get('error', 'Unknown error')}",
                    'error': result.get('error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Admin content scraping failed: {e}")
            return Response({
                'success': False,
                'message': f'Content scraping failed: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def content_status(self, request):
        """Get current content status and freshness information"""
        try:
            content_stats = self.wiki_service.content_manager.get_content_statistics()
            freshness_status = self.wiki_service.get_content_freshness_status()
            
            return Response({
                'success': True,
                'data': {
                    'content_statistics': content_stats,
                    'freshness_status': freshness_status,
                    'recommendations': self._get_content_recommendations(freshness_status)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting content status: {e}")
            return Response({
                'success': False,
                'message': f'Failed to get content status: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def clean_content(self, request):
        """Clean existing scraped content"""
        try:
            content_types = request.data.get('content_types', ['articles', 'timeline', 'glossary'])
            
            result = self.wiki_service.content_manager.clean_existing_content(content_types)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Content cleaned successfully',
                    'data': {
                        'deleted_counts': result.get('deleted_counts', {}),
                        'updated_stats': self.wiki_service.content_manager.get_content_statistics()
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': f"Content cleaning failed: {result.get('error', 'Unknown error')}",
                    'error': result.get('error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Content cleaning failed: {e}")
            return Response({
                'success': False,
                'message': f'Content cleaning failed: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """Clear content cache"""
        try:
            result = self.wiki_service.clear_content_cache()
            
            return Response({
                'success': True,
                'message': 'Content cache cleared successfully',
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            return Response({
                'success': False,
                'message': f'Cache clearing failed: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_content_recommendations(self, freshness_status):
        """Generate content management recommendations"""
        recommendations = []
        
        status = freshness_status.get('status', 'unknown')
        
        if status == 'never_scraped':
            recommendations.append({
                'priority': 'high',
                'action': 'initial_scraping',
                'message': 'Content has never been scraped. Run initial scraping to populate the database.'
            })
        elif status == 'stale':
            recommendations.append({
                'priority': 'medium',
                'action': 'refresh_content',
                'message': 'Content is stale. Consider refreshing to get latest information.'
            })
        elif status == 'aging':
            recommendations.append({
                'priority': 'low',
                'action': 'schedule_refresh',
                'message': 'Content is aging. Schedule a refresh in the near future.'
            })
        
        return recommendations


class WikiSearchViewSet(viewsets.ViewSet):
    """
    Enhanced search functionality using the content service
    """
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wiki_service = WikiContentService()

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Enhanced search across all content types"""
        query = request.query_params.get('q', '').strip()
        content_types = request.query_params.get('types', 'articles,glossary,timeline').split(',')
        
        if not query or len(query) < 2:
            return Response({
                'success': False,
                'message': 'Search query must be at least 2 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            results = self.wiki_service.search_content(query, content_types)
            
            return Response({
                'success': True,
                'query': query,
                'results': results,
                'total_results': sum(len(items) for items in results.values())
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return Response({
                'success': False,
                'message': f'Search failed: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
