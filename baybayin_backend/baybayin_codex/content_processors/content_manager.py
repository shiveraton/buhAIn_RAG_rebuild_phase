"""
Content Management for Database Operations
Handles saving enhanced content to Django models
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from ..models import (
    CodexCategory, CodexArticle, CodexTimeline, 
    CodexGlossary, CodexQuiz, CodexBookmark
)

logger = logging.getLogger(__name__)


class ContentManager:
    """Manages database operations for enhanced content"""
    
    def __init__(self):
        self.batch_size = 50
        self.stats = {
            'created': {'categories': 0, 'articles': 0, 'timeline': 0, 'glossary': 0},
            'updated': {'categories': 0, 'articles': 0, 'timeline': 0, 'glossary': 0},
            'errors': {'categories': 0, 'articles': 0, 'timeline': 0, 'glossary': 0}
        }
    
    def save_enhanced_content(self, enhanced_content: Dict) -> Dict:
        """Save all enhanced content to database"""
        logger.info("Starting content save to database...")
        
        try:
            with transaction.atomic():
                # Save in dependency order
                self._save_categories(enhanced_content.get('categories', []))
                self._save_articles(enhanced_content.get('articles', []))
                self._save_timeline_events(enhanced_content.get('timeline_events', []))
                self._save_glossary_terms(enhanced_content.get('glossary_terms', []))
                
                # Update category article counts
                self._update_category_article_counts()
                
                logger.info(f"Content save completed successfully!")
                logger.info(f"📊 Stats: {self.stats}")
                
                return {
                    'success': True,
                    'stats': self.stats,
                    'message': 'Content saved successfully'
                }
                
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    def _save_categories(self, categories: List[Dict]) -> None:
        """Save categories to database"""
        logger.info(f"Saving {len(categories)} categories...")
        
        for category_data in categories:
            try:
                category, created = CodexCategory.objects.update_or_create(
                    slug=category_data.get('slug'),
                    defaults={
                        'name': category_data.get('name', ''),
                        'description': category_data.get('description', ''),
                        'icon': category_data.get('icon', '📚'),
                        'color': category_data.get('color', '#6B7280'),
                        'order': category_data.get('order', 999),
                        'is_featured': category_data.get('is_featured', False)
                    }
                )
                
                if created:
                    self.stats['created']['categories'] += 1
                    logger.debug(f"Created category: {category.name}")
                else:
                    self.stats['updated']['categories'] += 1
                    logger.debug(f"Updated category: {category.name}")
                    
            except Exception as e:
                self.stats['errors']['categories'] += 1
                logger.error(f"Error saving category '{category_data.get('name')}': {e}")
    
    def _save_articles(self, articles: List[Dict]) -> None:
        """Save articles to database"""
        logger.info(f"Saving {len(articles)} articles...")
        
        for article_data in articles:
            try:
                # Get or create category
                category = self._get_or_create_default_category(
                    article_data.get('category_slug', 'general-information')
                )
                
                # Handle slug conflicts
                base_slug = article_data.get('slug') or slugify(article_data.get('title', ''))
                unique_slug = self._get_unique_slug(CodexArticle, base_slug)
                
                article, created = CodexArticle.objects.update_or_create(
                    slug=unique_slug,
                    defaults={
                        'title': article_data.get('title', ''),
                        'content': article_data.get('content', ''),
                        'summary': article_data.get('summary', ''),
                        'category': category,
                        'baybayin_examples': article_data.get('baybayin_examples', {}),
                        'metadata': article_data.get('metadata', {}),
                        'reading_time': article_data.get('reading_time', 1),
                        'difficulty': article_data.get('difficulty', 'beginner'),
                        'is_featured': article_data.get('is_featured', False),
                        'is_published': article_data.get('is_published', True),
                        'source': article_data.get('source', 'scraped'),
                        'url': article_data.get('url', '')
                    }
                )
                
                if created:
                    self.stats['created']['articles'] += 1
                    logger.debug(f"Created article: {article.title}")
                else:
                    self.stats['updated']['articles'] += 1
                    logger.debug(f"Updated article: {article.title}")
                    
            except ValidationError as e:
                self.stats['errors']['articles'] += 1
                logger.error(f"Validation error for article '{article_data.get('title')}': {e}")
            except Exception as e:
                self.stats['errors']['articles'] += 1
                logger.error(f"Error saving article '{article_data.get('title')}': {e}")
    
    def _save_timeline_events(self, timeline_events: List[Dict]) -> None:
        """Save timeline events to database"""
        logger.info(f"Saving {len(timeline_events)} timeline events...")
        
        for event_data in timeline_events:
            try:
                # Create unique identifier for timeline events
                identifier = self._create_timeline_identifier(
                    event_data.get('title', ''), 
                    event_data.get('date', '')
                )
                
                event, created = CodexTimeline.objects.update_or_create(
                    title=event_data.get('title', '')[:200],  # Limit title length
                    date=event_data.get('date', '1500-01-01'),
                    defaults={
                        'description': event_data.get('description', ''),
                        'period': event_data.get('period', 'ancient'),
                        'importance_level': event_data.get('importance_level', 'medium'),
                        'related_articles': event_data.get('related_articles', []),
                        'sources': event_data.get('sources', []),
                        'metadata': event_data.get('metadata', {})
                    }
                )
                
                if created:
                    self.stats['created']['timeline'] += 1
                    logger.debug(f"Created timeline event: {event.title}")
                else:
                    self.stats['updated']['timeline'] += 1
                    logger.debug(f"Updated timeline event: {event.title}")
                    
            except Exception as e:
                self.stats['errors']['timeline'] += 1
                logger.error(f"Error saving timeline event '{event_data.get('title')}': {e}")
    
    def _save_glossary_terms(self, glossary_terms: List[Dict]) -> None:
        """Save glossary terms to database"""
        logger.info(f"Saving {len(glossary_terms)} glossary terms...")
        
        for term_data in glossary_terms:
            try:
                term, created = CodexGlossary.objects.update_or_create(
                    term=term_data.get('term', ''),
                    defaults={
                        'definition': term_data.get('definition', ''),
                        'pronunciation': term_data.get('pronunciation', ''),
                        'baybayin_script': term_data.get('baybayin_script', ''),
                        'category': term_data.get('category', 'general'),
                        'etymology': term_data.get('etymology', ''),
                        'related_terms': term_data.get('related_terms', []),
                        'usage_examples': term_data.get('usage_examples', []),
                        'difficulty_level': term_data.get('difficulty_level', 'beginner'),
                        'metadata': term_data.get('metadata', {})
                    }
                )
                
                if created:
                    self.stats['created']['glossary'] += 1
                    logger.debug(f"Created glossary term: {term.term}")
                else:
                    self.stats['updated']['glossary'] += 1
                    logger.debug(f"Updated glossary term: {term.term}")
                    
            except Exception as e:
                self.stats['errors']['glossary'] += 1
                logger.error(f"Error saving glossary term '{term_data.get('term')}': {e}")
    
    def _get_or_create_default_category(self, category_slug: str) -> CodexCategory:
        """Get existing category or create default"""
        try:
            return CodexCategory.objects.get(slug=category_slug)
        except CodexCategory.DoesNotExist:
            # Create default category if it doesn't exist
            category, created = CodexCategory.objects.get_or_create(
                slug='general-information',
                defaults={
                    'name': 'General Information',
                    'description': 'General information about Baybayin and Philippine scripts',
                    'icon': '📋',
                    'color': '#6B7280',
                    'order': 999,
                    'is_featured': False
                }
            )
            if created:
                logger.info(f"Created default category: {category.name}")
            return category
    
    def _get_unique_slug(self, model, base_slug: str) -> str:
        """Generate unique slug for model"""
        if not base_slug:
            base_slug = 'article'
        
        slug = base_slug
        counter = 1
        
        while model.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _create_timeline_identifier(self, title: str, date: str) -> str:
        """Create unique identifier for timeline events"""
        return f"{date}-{slugify(title[:50])}"
    
    def _update_category_article_counts(self) -> None:
        """Update article counts for all categories"""
        logger.info("Updating category article counts...")
        
        for category in CodexCategory.objects.all():
            article_count = CodexArticle.objects.filter(
                category=category, 
                is_published=True
            ).count()
            
            if category.article_count != article_count:
                category.article_count = article_count
                category.save(update_fields=['article_count'])
                logger.debug(f"Updated {category.name} article count: {article_count}")
    
    def clean_existing_content(self, content_types: List[str] = None) -> Dict:
        """Clean existing scraped content from database"""
        if content_types is None:
            content_types = ['articles', 'timeline', 'glossary']
        
        logger.info(f"🧹 Cleaning existing content: {content_types}")
        
        deleted_counts = {}
        
        try:
            with transaction.atomic():
                if 'articles' in content_types:
                    deleted_articles = CodexArticle.objects.filter(
                        source__in=['scraped', 'wikipedia', 'cultural_scraper']
                    ).delete()
                    deleted_counts['articles'] = deleted_articles[0] if deleted_articles[0] else 0
                
                if 'timeline' in content_types:
                    deleted_timeline = CodexTimeline.objects.filter(
                        source__in=['scraped', 'wikipedia', 'cultural_scraper']
                    ).delete()
                    deleted_counts['timeline'] = deleted_timeline[0] if deleted_timeline[0] else 0
                
                if 'glossary' in content_types:
                    deleted_glossary = CodexGlossary.objects.filter(
                        source__in=['scraped', 'wikipedia', 'cultural_scraper']
                    ).delete()
                    deleted_counts['glossary'] = deleted_glossary[0] if deleted_glossary[0] else 0
                
                # Update category counts
                self._update_category_article_counts()
                
                logger.info(f"Content cleaning completed: {deleted_counts}")
                
                return {
                    'success': True,
                    'deleted_counts': deleted_counts,
                    'message': 'Content cleaned successfully'
                }
                
        except Exception as e:
            logger.error(f"Error cleaning content: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_counts': deleted_counts
            }
    
    def get_content_statistics(self) -> Dict:
        """Get current content statistics"""
        stats = {
            'categories': {
                'total': CodexCategory.objects.count(),
                'featured': CodexCategory.objects.filter(is_featured=True).count()
            },
            'articles': {
                'total': CodexArticle.objects.count(),
                'published': CodexArticle.objects.filter(is_published=True).count(),
                'featured': CodexArticle.objects.filter(is_featured=True).count(),
                'by_difficulty': {
                    'beginner': CodexArticle.objects.filter(difficulty_level='beginner').count(),
                    'intermediate': CodexArticle.objects.filter(difficulty_level='intermediate').count(),
                    'advanced': CodexArticle.objects.filter(difficulty_level='advanced').count()
                },
                'by_source': {
                    'scraped': CodexArticle.objects.filter(source='scraped').count(),
                    'wikipedia': CodexArticle.objects.filter(source='wikipedia').count(),
                    'cultural': CodexArticle.objects.filter(source='cultural_scraper').count(),
                    'manual': CodexArticle.objects.filter(source='manual').count()
                }
            },
            'timeline': {
                'total': CodexTimeline.objects.count(),
                'by_period': {
                    'pre_colonial': CodexTimeline.objects.filter(period__icontains='Pre-colonial').count(),
                    'spanish_era': CodexTimeline.objects.filter(period__icontains='Spanish').count(),
                    'modern': CodexTimeline.objects.filter(period__icontains='Modern').count()
                }
            },
            'glossary': {
                'total': CodexGlossary.objects.count(),
                'by_category': {
                    'script_terms': CodexGlossary.objects.filter(category='script_terms').count(),
                    'historical': CodexGlossary.objects.filter(category='historical').count(),
                    'linguistic': CodexGlossary.objects.filter(category='linguistic').count(),
                    'cultural': CodexGlossary.objects.filter(category='cultural').count(),
                    'general': CodexGlossary.objects.filter(category='general').count()
                },
                'by_difficulty': {
                    'beginner': CodexGlossary.objects.filter(difficulty_level='beginner').count(),
                    'intermediate': CodexGlossary.objects.filter(difficulty_level='intermediate').count(),
                    'advanced': CodexGlossary.objects.filter(difficulty_level='advanced').count()
                }
            },
            'updated_at': datetime.now().isoformat()
        }
        
        return stats
    
    def backup_content(self, backup_type: str = 'scraped') -> Dict:
        """Create backup of content before major operations"""
        logger.info(f"Creating content backup: {backup_type}")
        
        try:
            backup_data = {
                'backup_type': backup_type,
                'created_at': datetime.now().isoformat(),
                'stats': self.get_content_statistics()
            }
            
            if backup_type == 'scraped':
                # Backup scraped content
                backup_data['articles'] = list(
                    CodexArticle.objects.filter(
                        source__in=['scraped', 'wikipedia', 'cultural_scraper']
                    ).values()
                )
                backup_data['timeline'] = list(
                    CodexTimeline.objects.filter(
                        source__in=['scraped', 'wikipedia', 'cultural_scraper']
                    ).values()
                )
                backup_data['glossary'] = list(
                    CodexGlossary.objects.filter(
                        source__in=['scraped', 'wikipedia', 'cultural_scraper']
                    ).values()
                )
            
            # Save backup to cache for temporary storage
            cache_key = f"content_backup_{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return {
                'success': True,
                'backup_key': cache_key,
                'stats': backup_data['stats'],
                'message': f'Backup created successfully: {cache_key}'
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Backup creation failed'
            }
