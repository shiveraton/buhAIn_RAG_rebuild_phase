"""
Baybayin Wiki Content Service

This service handles content aggregation using self-hosted scrapers
and content processors for real-time educational content.
"""

import asyncio
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import models
from .models import WikiCategory, WikiArticle, WikiTimeline, WikiGlossary
from .scraper import scrape_wikipedia_articles, scrape_cultural_site, scrape_all
from .content_processors.content_enhancer import ContentEnhancer
from .content_processors.content_manager import ContentManager
import logging
import json

logger = logging.getLogger(__name__)


class WikiContentService:
    """Service for managing Baybayin wiki content using self-hosted scrapers"""
    
    def __init__(self):
        self.content_enhancer = ContentEnhancer()
        self.content_manager = ContentManager()
        
        # Cache settings
        self.cache_duration = getattr(settings, 'WIKI_CACHE_DURATION', 3600)  # 1 hour
        self.scraping_interval = getattr(settings, 'WIKI_SCRAPING_INTERVAL', 86400)  # 24 hours
        
        # Fallback data for when scraping fails
        self.fallback_enabled = getattr(settings, 'WIKI_FALLBACK_ENABLED', True)
    
    def scrape_and_update_content(self, force_refresh=False):
        """Scrape content from all sources and update database"""
        logger.info("Starting comprehensive content scraping and update...")
        
        # Check if we need to refresh based on last scraping time
        cache_key = 'last_content_scraping'
        last_scraping = cache.get(cache_key)
        
        if not force_refresh and last_scraping:
            time_since_last = timezone.now() - last_scraping
            if time_since_last.total_seconds() < self.scraping_interval:
                logger.info(f"Content is fresh, skipping scraping. Last update: {last_scraping}")
                return self._get_cached_stats()
        
        try:
            # Create content backup before scraping
            backup_result = self.content_manager.backup_content('scraped')
            logger.info(f"Backup created: {backup_result.get('message', 'Unknown')}")
            
            # Step 1: Scrape content from all sources
            scraped_data = self._scrape_all_sources()
            
            # Step 2: Enhance content for educational quality
            enhanced_content = self.content_enhancer.enhance_scraped_content(scraped_data)
            
            # Step 3: Save enhanced content to database
            save_result = self.content_manager.save_enhanced_content(enhanced_content)
            
            # Update cache timestamp
            cache.set(cache_key, timezone.now(), self.cache_duration * 24)  # Cache for 24 hours
            
            # Cache the results
            result = {
                'success': True,
                'scraping_completed_at': timezone.now().isoformat(),
                'save_result': save_result,
                'quality_report': enhanced_content.get('quality_report', {}),
                'content_stats': self.content_manager.get_content_statistics(),
                'message': 'Content scraping and update completed successfully'
            }
            
            cache.set('wiki_content_stats', result, self.cache_duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during content scraping: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Content scraping failed, using existing data'
            }
    
    def _scrape_all_sources(self):
        """Scrape content from all configured sources using scraper.py functions"""
        logger.info("Scraping content from all sources...")
        try:
            wiki_topics = [
                "Baybayin",
                "Prehistory of the Philippines",
                "Philippine scripts"
            ]
            cultural_sites = [
                {
                    'url': 'https://www.nationalmuseum.gov.ph/exhibitions/anthropology/baybayin/',
                    'article_selector': '.article-list .article',
                    'title_selector': '.article-title',
                    'content_selector': '.article-content'
                },
                {
                    'url': 'https://narrastudio.com/blogs/journal/baybayin-the-ancient-filipino-script-lives-on',
                    'article_selector': '.post',
                    'title_selector': '.post-title',
                    'content_selector': '.post-content'
                }
            ]
            articles = scrape_all(wiki_topics, cultural_sites)
            combined_data = {
                'categories': [],
                'articles': articles,
                'timeline_events': [],
                'glossary_terms': []
            }
            logger.info(f"Scraping completed. Total articles: {len(articles)}")
            return combined_data
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            if self.fallback_enabled:
                return self._get_fallback_data()
            else:
                raise
    
    def _merge_scraped_data(self, combined_data, source_data):
        """Merge data from a single source into combined data"""
        for key in ['categories', 'articles', 'timeline_events', 'glossary_terms']:
            if key in source_data:
                combined_data[key].extend(source_data[key])
    
    def get_content_freshness_status(self):
        """Get status of content freshness"""
        cache_key = 'last_content_scraping'
        last_scraping = cache.get(cache_key)
        
        if not last_scraping:
            return {
                'status': 'never_scraped',
                'message': 'Content has never been scraped',
                'action_needed': 'initial_scraping'
            }
        
        time_since_last = timezone.now() - last_scraping
        hours_since = time_since_last.total_seconds() / 3600
        
        if hours_since < 1:
            status = 'very_fresh'
        elif hours_since < 24:
            status = 'fresh'
        elif hours_since < 168:  # 1 week
            status = 'aging'
        else:
            status = 'stale'
        
        return {
            'status': status,
            'last_scraping': last_scraping.isoformat(),
            'hours_since_last': round(hours_since, 1),
            'action_needed': 'refresh' if status in ['aging', 'stale'] else 'none'
        }
    
    def _get_cached_stats(self):
        """Get cached content statistics"""
        cached_stats = cache.get('wiki_content_stats')
        if cached_stats:
            return cached_stats
        
        return {
            'success': True,
            'message': 'Using cached content statistics',
            'content_stats': self.content_manager.get_content_statistics(),
            'freshness': self.get_content_freshness_status()
        }
    
    
    def _get_fallback_data(self):
        """Return comprehensive fallback data when scraping fails"""
        logger.info("📋 Using fallback data due to scraping failure...")
        
        return {
            'categories': [
                {
                    'name': 'Origins and History',
                    'description': 'Explore the ancient origins and historical development of Baybayin script',
                    'slug': 'origins-history',
                    'icon': '📜',
                    'color': '#8B4513',
                    'order': 1,
                    'is_featured': True
                },
                {
                    'name': 'Script Mechanics',
                    'description': 'Learn how Baybayin characters, rules, and writing system work',
                    'slug': 'script-mechanics',
                    'icon': '⚙️',
                    'color': '#4169E1',
                    'order': 2,
                    'is_featured': True
                },
                {
                    'name': 'Linguistic Foundation',
                    'description': 'Understanding the linguistic principles behind Baybayin',
                    'slug': 'linguistic-foundation',
                    'icon': '📚',
                    'color': '#228B22',
                    'order': 3,
                    'is_featured': True
                },
                {
                    'name': 'Cultural Significance',
                    'description': 'Modern revival and cultural importance of Baybayin',
                    'slug': 'cultural-significance',
                    'icon': '🎭',
                    'color': '#FF6347',
                    'order': 4,
                    'is_featured': False
                }
            ],
            'articles': [
                {
                    'title': 'Introduction to Baybayin: The Ancient Script of the Philippines',
                    'content': '''Baybayin is a pre-colonial Philippine writing system that was widely used throughout the archipelago before Spanish colonization. This ancient script represents the rich literacy tradition of our ancestors and serves as a testament to the advanced civilization that existed in the Philippines long before foreign influence.

The script consists of 17 basic characters, each representing a syllable rather than individual letters. This syllabic nature makes Baybayin fundamentally different from the Latin alphabet we use today. Understanding Baybayin connects us to our cultural roots and helps preserve an important aspect of Philippine heritage.

Archaeological evidence suggests that Baybayin was used as early as the 14th century, with inscriptions found on various artifacts including the famous Laguna Copperplate Inscription dating to 900 CE. The script was not just ceremonial but was actively used for communication, record-keeping, and literature.

Learning Baybayin today represents more than acquiring a new skill—it's about reclaiming our cultural identity and honoring the wisdom of our ancestors. The modern revival of Baybayin demonstrates the Filipino people's commitment to preserving and celebrating their indigenous heritage.''',
                    'summary': 'An introduction to Baybayin, the ancient pre-colonial Philippine writing system, exploring its historical significance and cultural importance.',
                    'category_slug': 'origins-history',
                    'slug': 'introduction-baybayin-ancient-script',
                    'baybayin_examples': {
                        'scripts': [
                            {
                                'baybayin': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔',
                                'transliteration': 'Baybayin',
                                'context': 'The name of the ancient Philippine script'
                            }
                        ],
                        'transliterations': [
                            {'text': 'Baybayin', 'baybayin': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔'},
                            {'text': 'Pilipinas', 'baybayin': 'ᜉᜒᜎᜒᜉᜒᜈᜐ᜔'}
                        ]
                    },
                    'metadata': {
                        'author': 'BaybayinWiki Team',
                        'difficulty': 'beginner',
                        'educational_value': 0.9,
                        'credibility_score': 0.8,
                        'learning_objectives': [
                            'Understand the historical significance of Baybayin',
                            'Learn basic facts about the Philippine writing system',
                            'Appreciate the cultural importance of indigenous scripts'
                        ],
                        'tags': ['baybayin', 'philippine-scripts', 'history', 'culture', 'education']
                    },
                    'reading_time': 5,
                    'difficulty': 'beginner',
                    'is_featured': True,
                    'is_published': True,
                    'source': 'fallback',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            ],
            'timeline_events': [
                {
                    'title': 'First documented use of Baybayin script',
                    'description': 'Archaeological evidence shows early use of Baybayin-related scripts in the Philippines.',
                    'date': '1300-01-01',
                    'period': 'ancient',
                    'importance_level': 'high',
                    'related_articles': ['introduction-baybayin-ancient-script'],
                    'sources': ['Archaeological findings', 'Historical records'],
                    'metadata': {
                        'credibility': 'high',
                        'source': 'fallback'
                    }
                },
                {
                    'title': 'Spanish colonization begins',
                    'description': 'Spanish colonial rule begins, leading to the gradual decline of Baybayin usage as Latin script is introduced.',
                    'date': '1521-01-01',
                    'period': 'colonial',
                    'importance_level': 'high',
                    'related_articles': ['introduction-baybayin-ancient-script'],
                    'sources': ['Historical records'],
                    'metadata': {
                        'credibility': 'high',
                        'source': 'fallback'
                    }
                }
            ],
            'glossary_terms': [
                {
                    'term': 'Baybayin',
                    'definition': 'The pre-colonial Philippine writing system, also known as alibata, used to write various Philippine languages.',
                    'pronunciation': 'bai-ba-yin',
                    'baybayin_script': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔',
                    'category': 'script_terms',
                    'etymology': 'From the Tagalog word "baybay" meaning "to spell"',
                    'related_terms': ['Alibata', 'Suyat', 'Kudlit'],
                    'usage_examples': ['Learning Baybayin connects us to our heritage'],
                    'difficulty_level': 'beginner',
                    'metadata': {
                        'source': 'fallback'
                    }
                },
                {
                    'term': 'Kudlit',
                    'definition': 'Diacritical marks used in Baybayin to modify the inherent "a" vowel sound of characters.',
                    'pronunciation': 'kood-lit',
                    'baybayin_script': 'ᜃᜓᜇ᜔ᜎᜒᜆ᜔',
                    'category': 'script_terms',
                    'etymology': 'From Tagalog meaning "to make a mark"',
                    'related_terms': ['Baybayin', 'Vowel marks'],
                    'usage_examples': ['The kudlit changes the vowel sound from "a" to "i" or "u"'],
                    'difficulty_level': 'intermediate',
                    'metadata': {
                        'source': 'fallback'
                    }
                }
            ]
        }
    
    # Database query methods that work with scraped content
    def get_categories_from_db(self):
        """Get categories from database (populated by scrapers)"""
        cache_key = 'wiki_db_categories'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            categories = list(WikiCategory.objects.all().values(
                'id', 'name', 'description', 'slug', 'icon', 'color', 
                'order', 'is_featured', 'article_count'
            ))
            cache.set(cache_key, categories, self.cache_duration)
            return categories
        except Exception as e:
            logger.error(f"Error fetching categories from database: {e}")
            return []
    
    def get_articles_from_db(self, category_slug=None, difficulty=None, featured=None):
        """Get articles from database (populated by scrapers)"""
        cache_key = f'wiki_db_articles_{category_slug}_{difficulty}_{featured}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            queryset = WikiArticle.objects.filter(is_published=True)
            
            if category_slug:
                queryset = queryset.filter(category__slug=category_slug)
            if difficulty:
                queryset = queryset.filter(difficulty=difficulty)
            if featured is not None:
                queryset = queryset.filter(is_featured=featured)
            
            articles = list(queryset.select_related('category').values(
                'id', 'title', 'content', 'summary', 'slug', 'category__name',
                'category__slug', 'baybayin_examples', 'metadata', 
                'reading_time', 'difficulty', 'is_featured', 'source',
                'created_at', 'updated_at'
            ))
            
            cache.set(cache_key, articles, self.cache_duration)
            return articles
        except Exception as e:
            logger.error(f"Error fetching articles from database: {e}")
            return []
    
    def get_timeline_from_db(self):
        """Get timeline events from database (populated by scrapers)"""
        cache_key = 'wiki_db_timeline'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            timeline_events = list(WikiTimeline.objects.all().order_by('date').values(
                'id', 'title', 'description', 'date', 'period', 
                'importance_level', 'related_articles', 'sources', 'metadata'
            ))
            cache.set(cache_key, timeline_events, self.cache_duration)
            return timeline_events
        except Exception as e:
            logger.error(f"Error fetching timeline from database: {e}")
            return []
    
    def get_glossary_from_db(self, category=None, difficulty=None):
        """Get glossary terms from database (populated by scrapers)"""
        cache_key = f'wiki_db_glossary_{category}_{difficulty}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            queryset = WikiGlossary.objects.all()
            
            if category:
                queryset = queryset.filter(category=category)
            if difficulty:
                queryset = queryset.filter(difficulty_level=difficulty)
            
            glossary_terms = list(queryset.order_by('term').values(
                'id', 'term', 'definition', 'pronunciation', 'baybayin_script',
                'category', 'etymology', 'related_terms', 'usage_examples',
                'difficulty_level', 'metadata'
            ))
            
            cache.set(cache_key, glossary_terms, self.cache_duration)
            return glossary_terms
        except Exception as e:
            logger.error(f"Error fetching glossary from database: {e}")
            return []
    
    def get_featured_content(self):
        """Get featured content from database"""
        cache_key = 'wiki_featured_content'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            featured_content = {
                'categories': list(WikiCategory.objects.filter(is_featured=True).values()),
                'articles': list(WikiArticle.objects.filter(
                    is_featured=True, is_published=True
                ).select_related('category').values(
                    'id', 'title', 'summary', 'slug', 'category__name',
                    'reading_time', 'difficulty', 'baybayin_examples'
                )),
                'stats': {
                    'total_articles': WikiArticle.objects.filter(is_published=True).count(),
                    'total_categories': WikiCategory.objects.count(),
                    'total_timeline_events': WikiTimeline.objects.count(),
                    'total_glossary_terms': WikiGlossary.objects.count(),
                }
            }
            
            cache.set(cache_key, featured_content, self.cache_duration)
            return featured_content
        except Exception as e:
            logger.error(f"Error fetching featured content: {e}")
            return {
                'categories': [],
                'articles': [],
                'stats': {'total_articles': 0, 'total_categories': 0, 'total_timeline_events': 0, 'total_glossary_terms': 0}
            }
    
    def search_content(self, query, content_types=None):
        """Search content in database"""
        if not query or len(query.strip()) < 2:
            return {'articles': [], 'glossary': [], 'timeline': []}
        
        if content_types is None:
            content_types = ['articles', 'glossary', 'timeline']
        
        cache_key = f'wiki_search_{hash(query)}_{"|".join(content_types)}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            results = {}
            
            if 'articles' in content_types:
                results['articles'] = list(WikiArticle.objects.filter(
                    is_published=True
                ).filter(
                    models.Q(title__icontains=query) |
                    models.Q(content__icontains=query) |
                    models.Q(summary__icontains=query)
                ).select_related('category').values(
                    'id', 'title', 'summary', 'slug', 'category__name',
                    'reading_time', 'difficulty'
                )[:20])
            
            if 'glossary' in content_types:
                results['glossary'] = list(WikiGlossary.objects.filter(
                    models.Q(term__icontains=query) |
                    models.Q(definition__icontains=query)
                ).values(
                    'id', 'term', 'definition', 'pronunciation', 'baybayin_script'
                )[:10])
            
            if 'timeline' in content_types:
                results['timeline'] = list(WikiTimeline.objects.filter(
                    models.Q(title__icontains=query) |
                    models.Q(description__icontains=query)
                ).values(
                    'id', 'title', 'description', 'date', 'period'
                )[:10])
            
            cache.set(cache_key, results, self.cache_duration // 2)  # Cache search results for shorter time
            return results
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return {'articles': [], 'glossary': [], 'timeline': []}
    
    def clear_content_cache(self):
        """Clear all content-related cache"""
        cache_keys = [
            'wiki_db_categories',
            'wiki_db_articles_*',
            'wiki_db_timeline',
            'wiki_db_glossary_*',
            'wiki_featured_content',
            'wiki_content_stats',
            'last_content_scraping'
        ]
        
        # Clear specific cache keys
        for key in cache_keys:
            if '*' in key:
                # For wildcard keys, we'd need to implement cache key pattern matching
                # For now, just clear the known variations
                continue
            cache.delete(key)
        
        logger.info("Content cache cleared")
        return {'success': True, 'message': 'Content cache cleared successfully'}
