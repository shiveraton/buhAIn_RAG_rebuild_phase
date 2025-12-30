from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import PDFCodexEntry
from .serializers import PDFCodexEntryListSerializer, PDFCodexEntryDetailSerializer


class CodexPagination(PageNumberPagination):
    """Pagination for Codex articles"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PDFCodexViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet serving PDF content as 'articles' for Codex UI
    Mimics CodexArticleViewSet to maintain frontend compatibility
    """
    queryset = PDFCodexEntry.objects.all().order_by('page_number', 'chunk_index')
    permission_classes = [AllowAny]
    pagination_class = CodexPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text']
    ordering_fields = ['page_number', 'chunk_index', 'created_at']
    ordering = ['page_number', 'chunk_index']
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use detail serializer for single article view"""
        if self.action == 'retrieve':
            return PDFCodexEntryDetailSerializer
        return PDFCodexEntryListSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters
        Maintains compatibility with frontend filters
        """
        queryset = super().get_queryset()
        
        # Filter by page number if provided
        page_number = self.request.query_params.get('page_number')
        if page_number:
            queryset = queryset.filter(page_number=page_number)
        
        # Filter by category (all PDF content is same category)
        category = self.request.query_params.get('category')
        # Ignore category filter for PDF content
        
        # Filter by difficulty level (all same level)
        difficulty = self.request.query_params.get('difficulty_level')
        # Ignore difficulty filter for PDF content
        
        # Filter by featured (first chunk of each page)
        is_featured = self.request.query_params.get('is_featured')
        if is_featured == 'true':
            queryset = queryset.filter(chunk_index=0)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Enhanced search endpoint
        Compatible with CodexArticleViewSet search
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})
        
        # Search in text field
        results = self.queryset.filter(text__icontains=query)[:20]
        serializer = self.get_serializer(results, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured articles (first chunk of each page)
        """
        # Get one entry per page (chunk_index=0)
        queryset = self.queryset.filter(chunk_index=0)[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_page(self, request):
        """
        Get all chunks from a specific page
        """
        page_number = request.query_params.get('page_number')
        if not page_number:
            return Response(
                {'error': 'page_number parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.queryset.filter(page_number=page_number)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,  # Changed from 'chunks' to 'results'
            'page_number': page_number,
            'count': len(serializer.data)
        })
    
    @action(detail=False, methods=['post'])
    def semantic_search(self, request):
        """
        Perform semantic search across PDF entries.
        Compatible with the old CodexArticle semantic_search endpoint.
        
        Request body:
        {
            "query": "search query text",
            "top_k": 5,
            "min_similarity": 0.3
        }
        """
        try:
            from game_seg_trivia.retrieval_service import get_embedding_model
            import numpy as np
            
            query = request.data.get('query', '').strip()
            if not query:
                return Response({
                    'success': False,
                    'error': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            top_k = request.data.get('top_k', 10)
            min_similarity = request.data.get('min_similarity', 0.3)
            
            # Generate query embedding
            model = get_embedding_model()
            query_embedding = model.encode([query])[0]
            
            # Get all entries with embeddings in one query
            all_entries = PDFCodexEntry.objects.all()
            
            # Vectorized similarity computation
            embeddings = np.array([np.array(e.embedding) for e in all_entries])
            query_emb = np.array(query_embedding)
            
            # Compute all similarities at once (much faster!)
            norms = np.linalg.norm(embeddings, axis=1)
            query_norm = np.linalg.norm(query_emb)
            
            # Avoid division by zero
            valid_idx = (norms > 0) & (query_norm > 0)
            similarities = np.zeros(len(all_entries))
            similarities[valid_idx] = np.dot(embeddings[valid_idx], query_emb) / (norms[valid_idx] * query_norm)
            
            # Filter by min_similarity and get top_k
            valid_results = [(i, sim) for i, sim in enumerate(similarities) if sim >= min_similarity]
            valid_results.sort(key=lambda x: x[1], reverse=True)
            top_results = valid_results[:top_k]
            
            # Get the actual entries
            top_entries = [(all_entries[i], sim) for i, sim in top_results]
            
            # Serialize results
            serializer = self.get_serializer([e for e, _ in top_entries], many=True)
            
            # Format response to match old endpoint
            results = {
                'articles': [
                    {**data, 'similarity': float(top_entries[i][1])}
                    for i, data in enumerate(serializer.data)
                ],
                'facts': [],  # PDF entries are articles, not facts
                'combined': [
                    {**data, 'similarity': float(top_entries[i][1]), 'type': 'article'}
                    for i, data in enumerate(serializer.data)
                ]
            }
            
            return Response({
                'success': True,
                'query': query,
                'results': results,
                'total_articles': len(results['articles']),
                'total_facts': 0,
                'total_combined': len(results['combined'])
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
