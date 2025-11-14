"""
Unified RAG Service - Bridge between CodexArticle and TriviaSourceFact
Provides semantic search across both content types using monsoon-paraphrase-filipino
"""

from sentence_transformers import SentenceTransformer
from django.db.models import Q
import numpy as np
from typing import List, Dict, Any
import logging

from baybayin_codex.models import CodexArticle
from game_seg_trivia.models import TriviaSourceFact

logger = logging.getLogger(__name__)

# Unified embedding model
EMBEDDING_MODEL = 'monsoon-nlp/monsoon-paraphrase-filipino'


class UnifiedRAGService:
    """
    Unified Retrieval-Augmented Generation service for Baybayin Codex
    Searches across both CodexArticle and TriviaSourceFact using semantic similarity
    """
    
    def __init__(self):
        """Initialize the unified RAG service with shared embedding model"""
        try:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to load {EMBEDDING_MODEL}, using fallback: {e}")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 5, 
        include_articles: bool = True,
        include_facts: bool = True,
        min_similarity: float = 0.3
    ) -> Dict[str, Any]:
        """
        Perform semantic search across CodexArticles and TriviaSourceFacts
        
        Args:
            query: Search query text
            top_k: Number of results to return per source
            include_articles: Whether to search CodexArticles
            include_facts: Whether to search TriviaSourceFacts
            min_similarity: Minimum cosine similarity threshold (0-1)
        
        Returns:
            Dictionary with 'articles' and 'facts' lists, each containing ranked results
        """
        logger.info(f"Semantic search query: {query}")
        
        # Generate query embedding
        query_embedding = self.embedder.encode([query])[0]
        
        results = {
            'query': query,
            'articles': [],
            'facts': [],
            'combined': []
        }
        
        # Search CodexArticles
        if include_articles:
            article_results = self._search_codex_articles(query_embedding, top_k, min_similarity)
            results['articles'] = article_results
            results['combined'].extend([{**r, 'type': 'article'} for r in article_results])
        
        # Search TriviaSourceFacts
        if include_facts:
            fact_results = self._search_trivia_facts(query_embedding, top_k, min_similarity)
            results['facts'] = fact_results
            results['combined'].extend([{**r, 'type': 'fact'} for r in fact_results])
        
        # Sort combined results by similarity score
        results['combined'] = sorted(
            results['combined'], 
            key=lambda x: x['similarity_score'], 
            reverse=True
        )[:top_k * 2]  # Return top results from combined pool
        
        logger.info(f"Found {len(results['articles'])} articles, {len(results['facts'])} facts")
        
        return results
    
    def _search_codex_articles(
        self, 
        query_embedding: np.ndarray, 
        top_k: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Search CodexArticles using semantic similarity"""
        try:
            # Get published articles with embeddings (if stored)
            articles = CodexArticle.objects.filter(is_published=True).select_related('category')
            
            results = []
            for article in articles:
                # Generate embedding for article content
                article_text = f"{article.title} {article.summary} {article.content}"
                article_embedding = self.embedder.encode([article_text])[0]
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, article_embedding)
                
                if similarity >= min_similarity:
                    results.append({
                        'id': article.id,
                        'title': article.title,
                        'summary': article.summary,
                        'content_preview': article.content[:200] + '...' if len(article.content) > 200 else article.content,
                        'category': article.category.name if article.category else 'Uncategorized',
                        'difficulty': article.difficulty_level,
                        'similarity_score': float(similarity),
                        'tags': article.tags,
                        'reading_time': article.reading_time
                    })
            
            # Sort by similarity and return top_k
            results = sorted(results, key=lambda x: x['similarity_score'], reverse=True)[:top_k]
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching CodexArticles: {e}")
            return []
    
    def _search_trivia_facts(
        self, 
        query_embedding: np.ndarray, 
        top_k: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Search TriviaSourceFacts using semantic similarity"""
        try:
            facts = TriviaSourceFact.objects.select_related('source_archive').all()
            
            results = []
            for fact in facts:
                # Use stored embedding or generate new one
                if fact.embedding:
                    fact_embedding = np.array(fact.embedding)
                else:
                    fact_embedding = self.embedder.encode([fact.content])[0]
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, fact_embedding)
                
                if similarity >= min_similarity:
                    results.append({
                        'id': str(fact.id),
                        'content': fact.content,
                        'content_preview': fact.content[:200] + '...' if len(fact.content) > 200 else fact.content,
                        'source': fact.source_archive.title if fact.source_archive else 'Unknown',
                        'similarity_score': float(similarity),
                        'metadata': fact.metadata,
                        'token_count': fact.token_count
                    })
            
            # Sort by similarity and return top_k
            results = sorted(results, key=lambda x: x['similarity_score'], reverse=True)[:top_k]
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching TriviaSourceFacts: {e}")
            return []
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_related_articles(self, article_id: int, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find related articles based on semantic similarity to a given article
        
        Args:
            article_id: ID of the source article
            top_k: Number of related articles to return
        
        Returns:
            List of related articles with similarity scores
        """
        try:
            # Get source article
            source_article = CodexArticle.objects.get(id=article_id, is_published=True)
            
            # Create query from source article
            query_text = f"{source_article.title} {source_article.summary}"
            
            # Perform semantic search
            results = self.semantic_search(
                query=query_text,
                top_k=top_k + 1,  # Get one extra to exclude self
                include_articles=True,
                include_facts=False
            )
            
            # Filter out the source article itself
            related = [
                article for article in results['articles'] 
                if article['id'] != article_id
            ][:top_k]
            
            return related
            
        except CodexArticle.DoesNotExist:
            logger.warning(f"Article {article_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error finding related articles: {e}")
            return []


# Singleton instance
_rag_service_instance = None

def get_rag_service() -> UnifiedRAGService:
    """Get or create singleton RAG service instance"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = UnifiedRAGService()
    return _rag_service_instance
