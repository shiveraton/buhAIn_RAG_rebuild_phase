"""
Content Enhancement and Processing for Scraped Baybayin Content
Enhances, validates, and structures scraped content for educational use
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import re
from django.core.cache import cache
from ..models import CodexCategory, CodexArticle, CodexTimeline, CodexGlossary

logger = logging.getLogger(__name__)


class ContentEnhancer:
    """Enhances and processes scraped content for educational use"""
    
    def __init__(self):
        self.quality_thresholds = {
            'min_content_length': 200,
            'min_summary_length': 50,
            'max_title_length': 200,
            'min_credibility_score': 0.5
        }
        
        self.baybayin_patterns = {
            'unicode_range': r'[\u1700-\u171F]+',
            'transliteration_markers': [
                'baybayin', 'means', 'translates', 'reads as', 'pronounced',
                'written as', 'spelled', 'in tagalog'
            ]
        }
    
    def enhance_scraped_content(self, scraped_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Enhance all scraped content for educational quality"""
        logger.info("🧠 Starting content enhancement process...")
        
        enhanced_content = {
            'categories': self._enhance_categories(scraped_data.get('categories', [])),
            'articles': self._enhance_articles(scraped_data.get('articles', [])),
            'timeline_events': self._enhance_timeline(scraped_data.get('timeline_events', [])),
            'glossary_terms': self._enhance_glossary(scraped_data.get('glossary_terms', []))
        }
        
        # Add quality metrics
        enhanced_content['quality_report'] = self._generate_quality_report(enhanced_content)
        
        logger.info(f"✅ Content enhancement completed. Quality score: "
                   f"{enhanced_content['quality_report']['overall_score']:.2f}")
        
        return enhanced_content
    
    def _enhance_categories(self, categories: List[Dict]) -> List[Dict]:
        """Enhance category data"""
        enhanced_categories = []
        
        # Ensure we have standard categories
        standard_categories = self._get_standard_categories()
        
        for category in standard_categories:
            # Check if we have scraped content for this category
            existing_category = next((c for c in categories if c.get('slug') == category['slug']), None)
            
            if existing_category:
                # Merge scraped data with standard structure
                enhanced_category = {**category, **existing_category}
            else:
                enhanced_category = category
            
            # Add article count (will be calculated when saving)
            enhanced_category['article_count'] = 0
            
            enhanced_categories.append(enhanced_category)
        
        return enhanced_categories
    
    def _enhance_articles(self, articles: List[Dict]) -> List[Dict]:
        """Enhance article content for educational quality"""
        enhanced_articles = []
        
        for article in articles:
            try:
                enhanced_article = self._enhance_single_article(article)
                if enhanced_article and self._passes_quality_check(enhanced_article):
                    enhanced_articles.append(enhanced_article)
                else:
                    logger.warning(f"Article '{article.get('title', 'Unknown')}' failed quality check")
            except Exception as e:
                logger.error(f"Error enhancing article '{article.get('title', 'Unknown')}': {e}")
                continue
        
        # Sort articles by educational value
        enhanced_articles.sort(key=lambda x: x.get('educational_score', 0), reverse=True)
        
        return enhanced_articles
    
    def _enhance_single_article(self, article: Dict) -> Optional[Dict]:
        """Enhance individual article"""
        # Clean and validate content
        content = self._clean_content(article.get('content', ''))
        if len(content) < self.quality_thresholds['min_content_length']:
            return None
        
        # Enhance title
        title = self._enhance_title(article.get('title', ''))
        if not title:
            return None
        
        # Generate or enhance summary
        summary = self._enhance_summary(article.get('summary'), content)
        
        # Extract and enhance Baybayin examples
        baybayin_examples = self._enhance_baybayin_examples(
            article.get('baybayin_examples', {}), content
        )
        
        # Calculate educational metrics
        educational_metrics = self._calculate_educational_metrics(content, baybayin_examples)
        
        # Determine difficulty level
        difficulty = self._assess_difficulty(content, baybayin_examples)
        
        # Extract learning objectives
        learning_objectives = self._extract_learning_objectives(content, title)
        
        # Generate tags
        tags = self._generate_tags(content, title)
        
        enhanced_article = {
            'title': title,
            'content': content,
            'summary': summary,
            'category_slug': article.get('category_slug', 'general-information'),
            'slug': self._create_slug(title),
            'baybayin_examples': baybayin_examples,
            'metadata': {
                **article.get('metadata', {}),
                'enhanced_at': datetime.now().isoformat(),
                'source_count': 1,
                'credibility_score': self._calculate_credibility_score(article),
                'educational_value': educational_metrics['educational_value'],
                'completeness_score': educational_metrics['completeness_score'],
                'learning_objectives': learning_objectives,
                'tags': tags,
                'difficulty_factors': educational_metrics['difficulty_factors']
            },
            'reading_time': self._calculate_reading_time(content),
            'difficulty': difficulty,
            'educational_score': educational_metrics['educational_value'],
            'is_featured': self._determine_featured_status(article, educational_metrics),
            'is_published': True,
            'source': article.get('source', 'scraped'),
            'url': article.get('url', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return enhanced_article
    
    def _enhance_timeline(self, timeline_events: List[Dict]) -> List[Dict]:
        """Enhance timeline events"""
        enhanced_events = []
        
        for event in timeline_events:
            try:
                enhanced_event = self._enhance_single_timeline_event(event)
                if enhanced_event:
                    enhanced_events.append(enhanced_event)
            except Exception as e:
                logger.error(f"Error enhancing timeline event: {e}")
                continue
        
        # Sort by date
        enhanced_events.sort(key=lambda x: x.get('date', '0000-01-01'))
        
        # Remove duplicates
        enhanced_events = self._deduplicate_timeline_events(enhanced_events)
        
        return enhanced_events
    
    def _enhance_single_timeline_event(self, event: Dict) -> Optional[Dict]:
        """Enhance single timeline event"""
        title = event.get('title', '').strip()
        description = event.get('description', '').strip()
        
        if not title or not description or len(description) < 20:
            return None
        
        enhanced_event = {
            'title': title[:200],  # Limit title length
            'description': description,
            'date': event.get('date', '1500-01-01'),
            'period': event.get('period', 'ancient'),
            'importance_level': self._assess_importance_level(title, description),
            'related_articles': event.get('related_articles', []),
            'sources': event.get('sources', []),
            'metadata': {
                'enhanced_at': datetime.now().isoformat(),
                'credibility': event.get('credibility', 'medium'),
                'source': event.get('source', 'scraped')
            }
        }
        
        return enhanced_event
    
    def _enhance_glossary(self, glossary_terms: List[Dict]) -> List[Dict]:
        """Enhance glossary terms"""
        enhanced_terms = []
        
        for term in glossary_terms:
            try:
                enhanced_term = self._enhance_single_glossary_term(term)
                if enhanced_term:
                    enhanced_terms.append(enhanced_term)
            except Exception as e:
                logger.error(f"Error enhancing glossary term: {e}")
                continue
        
        # Remove duplicates and sort
        enhanced_terms = self._deduplicate_glossary_terms(enhanced_terms)
        enhanced_terms.sort(key=lambda x: x.get('term', '').lower())
        
        return enhanced_terms
    
    def _enhance_single_glossary_term(self, term: Dict) -> Optional[Dict]:
        """Enhance single glossary term"""
        term_text = term.get('term', '').strip()
        definition = term.get('definition', '').strip()
        
        if not term_text or not definition or len(definition) < 10:
            return None
        
        enhanced_term = {
            'term': term_text.title(),
            'definition': definition,
            'pronunciation': term.get('pronunciation', '') or self._generate_pronunciation(term_text),
            'baybayin_script': term.get('baybayin_script', ''),
            'category': self._categorize_term(term_text, definition),
            'etymology': term.get('etymology', ''),
            'related_terms': term.get('related_terms', []),
            'usage_examples': term.get('usage_examples', []),
            'difficulty_level': self._assess_term_difficulty(definition),
            'metadata': {
                'enhanced_at': datetime.now().isoformat(),
                'source': term.get('source', 'scraped')
            }
        }
        
        return enhanced_term
    
    def _clean_content(self, content: str) -> str:
        """Clean and standardize content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove unwanted characters and formatting
        content = re.sub(r'[\r\n\t]+', '\n', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # Remove navigation elements and common webpage artifacts
        unwanted_phrases = [
            'click here', 'read more', 'continue reading', 'share this',
            'follow us', 'subscribe', 'advertisement', 'cookies policy'
        ]
        
        for phrase in unwanted_phrases:
            content = re.sub(rf'\b{re.escape(phrase)}\b', '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _enhance_title(self, title: str) -> str:
        """Enhance and validate title"""
        if not title:
            return ""
        
        # Clean title
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['Wikipedia:', 'Article:', 'Page:']
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        # Limit length
        if len(title) > self.quality_thresholds['max_title_length']:
            title = title[:self.quality_thresholds['max_title_length']] + '...'
        
        return title
    
    def _enhance_summary(self, existing_summary: str, content: str) -> str:
        """Generate or enhance article summary"""
        if existing_summary and len(existing_summary) >= self.quality_thresholds['min_summary_length']:
            return existing_summary
        
        # Generate summary from content
        sentences = content.split('.')
        summary_sentences = []
        
        for sentence in sentences[:5]:
            sentence = sentence.strip()
            if (len(sentence) > 30 and 
                not sentence.lower().startswith(('the following', 'click', 'see also'))):
                summary_sentences.append(sentence)
                if len(summary_sentences) >= 3:
                    break
        
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary or "Educational content about Baybayin and Philippine writing systems."
    
    def _enhance_baybayin_examples(self, existing_examples: Dict, content: str) -> Dict:
        """Enhance Baybayin examples in content"""
        enhanced_examples = existing_examples.copy() if existing_examples else {}
        
        # Extract additional Baybayin text from content
        baybayin_pattern = self.baybayin_patterns['unicode_range']
        baybayin_matches = re.finditer(baybayin_pattern, content)
        
        scripts = enhanced_examples.get('scripts', [])
        
        for match in baybayin_matches:
            baybayin_text = match.group()
            context_start = max(0, match.start() - 100)
            context_end = min(len(content), match.end() + 100)
            context = content[context_start:context_end]
            
            # Avoid duplicates
            if not any(script.get('baybayin') == baybayin_text for script in scripts):
                scripts.append({
                    'baybayin': baybayin_text,
                    'context': context,
                    'transliteration': self._find_transliteration(baybayin_text, context)
                })
        
        enhanced_examples['scripts'] = scripts
        
        # Enhance transliterations
        if 'transliterations' not in enhanced_examples:
            enhanced_examples['transliterations'] = []
        
        # Add common Baybayin examples if none exist
        if not enhanced_examples.get('scripts') and not enhanced_examples.get('transliterations'):
            enhanced_examples.update(self._get_default_baybayin_examples())
        
        return enhanced_examples
    
    def _find_transliteration(self, baybayin_text: str, context: str) -> str:
        """Find transliteration for Baybayin text in context"""
        # Look for transliteration patterns in context
        patterns = [
            rf'{re.escape(baybayin_text)}\s*[:\-–]\s*([A-Za-z\s]+)',
            rf'([A-Za-z\s]+)\s*[:\-–]\s*{re.escape(baybayin_text)}',
            rf'{re.escape(baybayin_text)}\s*\([^)]*([A-Za-z\s]+)[^)]*\)',
            rf'means\s+"([^"]+)".*{re.escape(baybayin_text)}',
            rf'{re.escape(baybayin_text)}.*means\s+"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _calculate_educational_metrics(self, content: str, baybayin_examples: Dict) -> Dict:
        """Calculate educational value metrics"""
        word_count = len(content.split())
        
        # Educational value factors
        has_examples = bool(baybayin_examples.get('scripts') or baybayin_examples.get('transliterations'))
        has_historical_context = any(term in content.lower() for term in 
            ['history', 'historical', 'ancient', 'colonial', 'traditional'])
        has_practical_info = any(term in content.lower() for term in 
            ['learn', 'practice', 'use', 'write', 'read', 'tutorial'])
        has_cultural_context = any(term in content.lower() for term in 
            ['culture', 'cultural', 'tradition', 'heritage', 'significance'])
        
        # Calculate scores
        educational_value = 0.0
        if has_examples:
            educational_value += 0.3
        if has_historical_context:
            educational_value += 0.25
        if has_practical_info:
            educational_value += 0.25
        if has_cultural_context:
            educational_value += 0.2
        
        # Content length factor
        length_factor = min(1.0, word_count / 500)  # Optimal around 500 words
        educational_value *= length_factor
        
        # Completeness score
        completeness_score = 0.0
        if word_count > 200:
            completeness_score += 0.3
        if has_examples:
            completeness_score += 0.4
        if has_historical_context and has_cultural_context:
            completeness_score += 0.3
        
        return {
            'educational_value': educational_value,
            'completeness_score': completeness_score,
            'difficulty_factors': {
                'word_count': word_count,
                'has_examples': has_examples,
                'has_historical_context': has_historical_context,
                'has_practical_info': has_practical_info
            }
        }
    
    def _assess_difficulty(self, content: str, baybayin_examples: Dict) -> str:
        """Assess content difficulty level"""
        word_count = len(content.split())
        
        # Count complex words (8+ characters)
        words = content.split()
        complex_words = [w for w in words if len(w) >= 8]
        complexity_ratio = len(complex_words) / len(words) if words else 0
        
        # Check for advanced concepts
        advanced_terms = ['linguistic', 'orthographic', 'phonetic', 'morphological', 
                         'etymology', 'historical linguistics', 'paleography']
        has_advanced_concepts = any(term in content.lower() for term in advanced_terms)
        
        # Determine difficulty
        if word_count < 300 and complexity_ratio < 0.15 and not has_advanced_concepts:
            return 'beginner'
        elif word_count < 800 and complexity_ratio < 0.25:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _extract_learning_objectives(self, content: str, title: str) -> List[str]:
        """Extract learning objectives from content"""
        objectives = []
        
        # Based on content type and topic
        if 'history' in title.lower() or 'origin' in title.lower():
            objectives.append("Understand the historical development of Baybayin")
            if 'colonial' in content.lower():
                objectives.append("Learn about the impact of colonization on native scripts")
        
        if 'script' in title.lower() or 'writing' in title.lower():
            objectives.append("Learn the mechanics of Baybayin writing system")
            if 'character' in content.lower():
                objectives.append("Recognize and understand Baybayin characters")
        
        if 'culture' in title.lower() or 'significance' in title.lower():
            objectives.append("Appreciate the cultural significance of Baybayin")
        
        # Add general objectives
        if not objectives:
            objectives.append("Gain knowledge about Philippine indigenous writing systems")
        
        return objectives
    
    def _generate_tags(self, content: str, title: str) -> List[str]:
        """Generate relevant tags for content"""
        tags = set()
        
        # Topic-based tags
        topic_tags = {
            'history': ['historical', 'ancient', 'origins'],
            'script': ['writing-system', 'characters', 'literacy'],
            'culture': ['cultural-heritage', 'tradition', 'identity'],
            'language': ['linguistics', 'tagalog', 'philippine-languages'],
            'colonial': ['spanish-period', 'colonization', 'cultural-impact'],
            'modern': ['revival', 'contemporary', 'preservation']
        }
        
        content_lower = content.lower()
        title_lower = title.lower()
        
        for topic, related_tags in topic_tags.items():
            if topic in content_lower or topic in title_lower:
                tags.update(related_tags)
        
        # Always include base tags
        tags.update(['baybayin', 'philippine-scripts', 'education'])
        
        return list(tags)
    
    def _calculate_credibility_score(self, article: Dict) -> float:
        """Calculate credibility score for article"""
        source = article.get('source', '').lower()
        
        # Source credibility mapping
        source_scores = {
            'wikipedia': 0.8,
            'ncca': 0.95,  # Government cultural agency
            'nhcp': 0.95,  # Government historical commission
            'national_museum': 0.9,
            'cultural_center_philippines': 0.85,
            'academic': 0.9,
            'university': 0.85
        }
        
        base_score = source_scores.get(source, 0.6)
        
        # Adjust based on metadata
        metadata = article.get('metadata', {})
        if metadata.get('references'):
            base_score += 0.1
        if metadata.get('author'):
            base_score += 0.05
        
        return min(1.0, base_score)
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate reading time in minutes"""
        word_count = len(content.split())
        # Average reading speed: 200-250 words per minute
        return max(1, word_count // 200)
    
    def _determine_featured_status(self, article: Dict, educational_metrics: Dict) -> bool:
        """Determine if article should be featured"""
        title = article.get('title', '').lower()
        educational_value = educational_metrics.get('educational_value', 0)
        
        # Feature if high educational value or key topic
        key_topics = ['baybayin', 'ancient script', 'philippine writing', 'pre-colonial']
        is_key_topic = any(topic in title for topic in key_topics)
        
        return educational_value > 0.7 or is_key_topic
    
    def _passes_quality_check(self, article: Dict) -> bool:
        """Check if article meets quality thresholds"""
        content = article.get('content', '')
        title = article.get('title', '')
        credibility = article.get('metadata', {}).get('credibility_score', 0)
        
        return (len(content) >= self.quality_thresholds['min_content_length'] and
                len(title) > 0 and
                credibility >= self.quality_thresholds['min_credibility_score'])
    
    def _get_standard_categories(self) -> List[Dict]:
        """Get standard category structure"""
        return [
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
            },
            {
                'name': 'Learning Resources',
                'description': 'Practical guides and exercises for learning Baybayin',
                'slug': 'learning-resources',
                'icon': '🎓',
                'color': '#9370DB',
                'order': 5,
                'is_featured': False
            },
            {
                'name': 'General Information',
                'description': 'Additional information and miscellaneous topics',
                'slug': 'general-information',
                'icon': '📋',
                'color': '#708090',
                'order': 6,
                'is_featured': False
            }
        ]
    
    def _get_default_baybayin_examples(self) -> Dict:
        """Get default Baybayin examples when none are found"""
        return {
            'scripts': [
                {
                    'baybayin': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔',
                    'transliteration': 'Baybayin',
                    'context': 'The ancient script of the Philippines'
                }
            ],
            'transliterations': [
                {
                    'text': 'Baybayin',
                    'baybayin': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔'
                }
            ]
        }
    
    def _create_slug(self, title: str) -> str:
        """Create URL-friendly slug"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _assess_importance_level(self, title: str, description: str) -> str:
        """Assess importance level of timeline event"""
        high_importance_keywords = ['first', 'established', 'founded', 'discovered', 
                                   'colonial', 'spanish', 'major', 'significant']
        
        text = (title + ' ' + description).lower()
        
        if any(keyword in text for keyword in high_importance_keywords):
            return 'high'
        elif any(keyword in text for keyword in ['important', 'notable', 'key']):
            return 'medium'
        else:
            return 'low'
    
    def _categorize_term(self, term: str, definition: str) -> str:
        """Categorize glossary term"""
        term_lower = term.lower()
        definition_lower = definition.lower()
        
        if any(word in term_lower for word in ['script', 'writing', 'character']):
            return 'script_terms'
        elif any(word in definition_lower for word in ['history', 'historical', 'ancient']):
            return 'historical'
        elif any(word in definition_lower for word in ['language', 'linguistic', 'grammar']):
            return 'linguistic'
        elif any(word in definition_lower for word in ['culture', 'cultural', 'tradition']):
            return 'cultural'
        else:
            return 'general'
    
    def _assess_term_difficulty(self, definition: str) -> str:
        """Assess difficulty level of glossary term"""
        word_count = len(definition.split())
        
        if word_count < 15:
            return 'beginner'
        elif word_count < 30:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _generate_pronunciation(self, term: str) -> str:
        """Generate pronunciation guide for term"""
        pronunciation_map = {
            'baybayin': 'bai-ba-yin',
            'alibata': 'ah-li-ba-ta',
            'kudlit': 'kood-lit',
            'tagalog': 'ta-ga-log',
            'suyat': 'soo-yat',
            'sulat': 'soo-lat'
        }
        
        return pronunciation_map.get(term.lower(), '')
    
    def _deduplicate_timeline_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate timeline events"""
        seen_events = set()
        unique_events = []
        
        for event in events:
            event_key = (event.get('title', ''), event.get('date', ''))
            if event_key not in seen_events:
                seen_events.add(event_key)
                unique_events.append(event)
        
        return unique_events
    
    def _deduplicate_glossary_terms(self, terms: List[Dict]) -> List[Dict]:
        """Remove duplicate glossary terms"""
        seen_terms = set()
        unique_terms = []
        
        for term in terms:
            term_key = term.get('term', '').lower()
            if term_key not in seen_terms and term_key:
                seen_terms.add(term_key)
                unique_terms.append(term)
        
        return unique_terms
    
    def _generate_quality_report(self, enhanced_content: Dict) -> Dict:
        """Generate quality report for enhanced content"""
        total_articles = len(enhanced_content.get('articles', []))
        featured_articles = len([a for a in enhanced_content.get('articles', []) 
                                if a.get('is_featured', False)])
        
        high_quality_articles = len([a for a in enhanced_content.get('articles', [])
                                    if a.get('educational_score', 0) > 0.7])
        
        overall_score = 0.0
        if total_articles > 0:
            overall_score = (high_quality_articles / total_articles) * 0.7
            if featured_articles > 0:
                overall_score += (featured_articles / total_articles) * 0.3
        
        return {
            'total_articles': total_articles,
            'featured_articles': featured_articles,
            'high_quality_articles': high_quality_articles,
            'overall_score': overall_score,
            'categories_count': len(enhanced_content.get('categories', [])),
            'timeline_events_count': len(enhanced_content.get('timeline_events', [])),
            'glossary_terms_count': len(enhanced_content.get('glossary_terms', [])),
            'generated_at': datetime.now().isoformat()
        }
