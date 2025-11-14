from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import (
    CodexCategory, CodexArticle, CodexTimeline, CodexGlossary, 
    CodexQuiz, CodexBookmark, CodexReadingProgress
)
from .serializers import (
    CodexCategorySerializer, CodexArticleListSerializer, CodexArticleDetailSerializer,
    CodexTimelineSerializer, CodexGlossarySerializer, CodexQuizSerializer,
    CodexBookmarkSerializer, CodexReadingProgressSerializer
)
from .services import CodexContentService
from .rag_service import get_rag_service
import logging

logger = logging.getLogger(__name__)



# CodexCategoryViewSet
class CodexCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for codex categories with article counts"""
    serializer_class = CodexCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'article_count']
    ordering = ['order', 'name']

    def get_queryset(self):
        return CodexCategory.objects.all()

# CodexArticleViewSet
class CodexArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for codex articles with list and detail views"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty_level', 'is_featured']
    search_fields = ['title', 'content', 'summary', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'reading_time']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_queryset(self):
        return CodexArticle.objects.filter(is_published=True).select_related('category')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CodexArticleDetailSerializer
        return CodexArticleListSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Toggle bookmark for an article"""
        article = self.get_object()
        bookmark, created = CodexBookmark.objects.get_or_create(
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
        progress, created = CodexReadingProgress.objects.get_or_create(
            user=request.user,
            article=article,
            defaults={'progress_percentage': percentage}
        )
        if not created:
            progress.progress_percentage = percentage
            progress.completed = percentage >= 100
            progress.save()
        serializer = CodexReadingProgressSerializer(progress)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def semantic_search(self, request):
        """
        Perform semantic search across CodexArticles and TriviaSourceFacts using RAG.
        Returns ranked articles with relevance scores.
        
        Request body:
        {
            "query": "search query text",
            "top_k": 5,  # optional, default 5
            "include_facts": true,  # optional, default true
            "min_similarity": 0.3  # optional, default 0.3
        }
        """
        try:
            query = request.data.get('query', '').strip()
            if not query:
                return Response({
                    'success': False,
                    'error': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            top_k = request.data.get('top_k', 5)
            include_facts = request.data.get('include_facts', True)
            min_similarity = request.data.get('min_similarity', 0.3)
            
            # Get RAG service instance
            rag_service = get_rag_service()
            
            # Perform semantic search
            results = rag_service.semantic_search(
                query=query,
                top_k=top_k,
                include_articles=True,
                include_facts=include_facts,
                min_similarity=min_similarity
            )
            
            return Response({
                'success': True,
                'query': query,
                'results': results,
                'total_articles': len(results['articles']),
                'total_facts': len(results['facts']),
                'total_combined': len(results['combined'])
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def related_articles(self, request, pk=None):
        """
        Get related articles based on semantic similarity to the current article.
        """
        try:
            article = self.get_object()
            top_k = int(request.query_params.get('top_k', 3))
            
            # Get RAG service instance
            rag_service = get_rag_service()
            
            # Get related articles
            related = rag_service.get_related_articles(
                article_id=article.id,
                top_k=top_k
            )
            
            return Response({
                'success': True,
                'article_id': article.id,
                'article_title': article.title,
                'related_articles': related
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Related articles error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CodexTimelineViewSet
class CodexTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for historical timeline events"""
    queryset = CodexTimeline.objects.all()
    serializer_class = CodexTimelineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['year', 'importance', 'period']
    search_fields = ['title', 'description']
    ordering_fields = ['year', 'importance', 'created_at']
    ordering = ['year']

# CodexGlossaryViewSet
class CodexGlossaryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for glossary terms"""
    queryset = CodexGlossary.objects.all()
    serializer_class = CodexGlossarySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty_level']
    search_fields = ['term', 'definition', 'pronunciation']
    ordering_fields = ['term', 'created_at']
    ordering = ['term']

# CodexQuizViewSet
class CodexQuizViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for quiz questions"""
    queryset = CodexQuiz.objects.select_related('article').all()
    serializer_class = CodexQuizSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['article', 'difficulty']
    search_fields = ['question', 'explanation']
    ordering_fields = ['created_at', 'difficulty']
    ordering = ['created_at']

# CodexBookmarkViewSet
class CodexBookmarkViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user bookmarks"""
    serializer_class = CodexBookmarkSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['article__category']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return CodexBookmark.objects.filter(user=self.request.user).select_related('article')


class CodexReadingProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading progress
    """
    serializer_class = CodexReadingProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['completed', 'article__category']
    ordering_fields = ['last_read_at', 'progress_percentage']
    ordering = ['-last_read_at']
    
    def get_queryset(self):
        return CodexReadingProgress.objects.filter(user=self.request.user).select_related('article')


class CodexStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for codex statistics
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get codex overview statistics"""
        stats = {
            'total_articles': CodexArticle.objects.filter(is_published=True).count(),
            'total_categories': CodexCategory.objects.count(),
            'total_timeline_events': CodexTimeline.objects.count(),
            'total_glossary_terms': CodexGlossary.objects.count(),
            'featured_articles': CodexArticle.objects.filter(is_featured=True, is_published=True).count(),
        }
        
        if request.user.is_authenticated:
            stats.update({
                'bookmarked_articles': CodexBookmark.objects.filter(user=request.user).count(),
                'completed_articles': CodexReadingProgress.objects.filter(
                    user=request.user, completed=True
                ).count(),
            })
        
        return Response(stats)


class CodexContentManagementViewSet(viewsets.ViewSet):
    """
    Admin ViewSet for managing codex content scraping and updates
    """
    permission_classes = [IsAdminUser]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.codex_service = CodexContentService()

    @action(detail=False, methods=['post'])
    def scrape_content(self, request):
        """Trigger content scraping from all sources"""
        try:
            force_refresh = request.data.get('force_refresh', False)
            logger.info(f"Content scraping triggered by admin. Force refresh: {force_refresh}")
            
            result = self.codex_service.scrape_and_update_content(force_refresh=force_refresh)
            
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
            content_stats = self.codex_service.content_manager.get_content_statistics()
            freshness_status = self.codex_service.get_content_freshness_status()
            
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
            
            result = self.codex_service.content_manager.clean_existing_content(content_types)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Content cleaned successfully',
                    'data': {
                        'deleted_counts': result.get('deleted_counts', {}),
                        'updated_stats': self.codex_service.content_manager.get_content_statistics()
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
            result = self.codex_service.clear_content_cache()
            
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

class CodexSearchViewSet(viewsets.ViewSet):
    """
    Enhanced search functionality using the codex content service
    """
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.codex_service = CodexContentService()

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
            results = self.codex_service.search_content(query, content_types)
            
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
