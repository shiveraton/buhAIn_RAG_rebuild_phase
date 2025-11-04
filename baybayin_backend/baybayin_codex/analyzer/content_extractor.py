"""
Content Extractor for Baybayin Documents
Handles content extraction, processing, and formatting for user-curated repositories
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from django.conf import settings
from ..models import CodexArticle, CodexCategory, CodexGlossary
from text_transliteration.services import TransliterationService
from text_transliteration.preprocessing.services import TextPreprocessingService

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Extracts and processes content from analyzed documents"""
    
    def __init__(self):
        self.transliteration_service = TransliterationService()
        self.preprocessing_service = TextPreprocessingService()
        
        # Baybayin content patterns
        self.baybayin_patterns = [
            r'[\u1700-\u171F]+',  # Tagalog Unicode block
            r'(?i)\b(?:baybayin|alibata|script|syllable|character)\b',
            r'(?i)\b(?:tagalog|filipino|pilipino|philippines)\b.*(?:writing|script|alphabet)',
        ]
        
        # Content quality thresholds
        self.min_content_length = 100
        self.min_baybayin_relevance = 0.3
        
    def extract_structured_content(self, analysis_result: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Extract structured content from document analysis results
        
        Args:
            analysis_result: Results from PDF or image analysis
            user_id: ID of the user who uploaded the document
            
        Returns:
            Dictionary containing structured content ready for database storage
        """
        try:
            logger.info(f"Extracting structured content for user {user_id}")
            
            extracted_content = {
                'articles': [],
                'glossary_terms': [],
                'timeline_events': [],
                'metadata': {
                    'extraction_timestamp': datetime.now().isoformat(),
                    'user_id': user_id,
                    'source_file': analysis_result.get('file_info', {}).get('filename', 'unknown'),
                    'content_quality_score': 0.0,
                    'baybayin_relevance_score': 0.0
                }
            }
            
            # Extract text content
            text_content = self._consolidate_text_content(analysis_result.get('text_content', {}))
            
            if not text_content or len(text_content) < self.min_content_length:
                logger.warning("Insufficient text content extracted")
                return extracted_content
            
            # Calculate content quality and relevance scores
            quality_score = self._calculate_content_quality(text_content, analysis_result)
            relevance_score = self._calculate_baybayin_relevance(text_content, analysis_result)
            
            extracted_content['metadata']['content_quality_score'] = quality_score
            extracted_content['metadata']['baybayin_relevance_score'] = relevance_score
            
            # Only process if content meets minimum quality thresholds
            if quality_score < 0.5 or relevance_score < self.min_baybayin_relevance:
                logger.warning(f"Content quality ({quality_score}) or relevance ({relevance_score}) below threshold")
                return extracted_content
            
            # Extract articles
            articles = self._extract_articles(text_content, analysis_result, user_id)
            extracted_content['articles'] = articles
            
            # Extract glossary terms
            glossary_terms = self._extract_glossary_terms(text_content, analysis_result)
            extracted_content['glossary_terms'] = glossary_terms
            
            # Extract timeline events
            timeline_events = self._extract_timeline_events(text_content, analysis_result)
            extracted_content['timeline_events'] = timeline_events
            
            logger.info(f"Content extraction completed: {len(articles)} articles, {len(glossary_terms)} terms, {len(timeline_events)} events")
            return extracted_content
            
        except Exception as e:
            logger.error(f"Error extracting structured content: {e}")
            return {'error': f'Content extraction failed: {str(e)}'}
    
    def _consolidate_text_content(self, text_content: Dict[str, Any]) -> str:
        """Consolidate text from various OCR methods"""
        consolidated_text = ""
        
        # Combine text from different extraction methods
        for method, content in text_content.items():
            if isinstance(content, str) and content.strip():
                consolidated_text += f"\n{content.strip()}\n"
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, str) and item.strip():
                        consolidated_text += f"\n{item.strip()}\n"
        
        # Clean and normalize the text
        consolidated_text = self.preprocessing_service.clean_text(consolidated_text)
        return consolidated_text.strip()
    
    def _calculate_content_quality(self, text_content: str, analysis_result: Dict[str, Any]) -> float:
        """Calculate content quality score based on various factors"""
        score = 0.0
        
        # Text length factor (longer content usually better)
        length_score = min(len(text_content) / 1000, 1.0)
        score += length_score * 0.3
        
        # OCR confidence if available
        ocr_confidence = analysis_result.get('text_content', {}).get('confidence', 0.5)
        score += float(ocr_confidence) * 0.3
        
        # Presence of structured content (headers, lists, etc.)
        structure_score = self._analyze_content_structure(text_content)
        score += structure_score * 0.2
        
        # Language quality (grammar, spelling)
        language_score = self._analyze_language_quality(text_content)
        score += language_score * 0.2
        
        return min(score, 1.0)
    
    def _calculate_baybayin_relevance(self, text_content: str, analysis_result: Dict[str, Any]) -> float:
        """Calculate how relevant the content is to Baybayin"""
        relevance_score = 0.0
        
        # Check for Baybayin-related keywords
        keyword_matches = 0
        baybayin_keywords = [
            'baybayin', 'alibata', 'tagalog script', 'filipino script',
            'pre-colonial', 'ancient writing', 'syllabic script',
            'kudlit', 'virama', 'consonant cluster'
        ]
        
        text_lower = text_content.lower()
        for keyword in baybayin_keywords:
            if keyword in text_lower:
                keyword_matches += 1
        
        relevance_score += min(keyword_matches / len(baybayin_keywords), 0.5)
        
        # Check for Unicode Baybayin characters
        baybayin_chars = re.findall(r'[\u1700-\u171F]', text_content)
        if baybayin_chars:
            relevance_score += 0.3
        
        # Check visual analysis for script characteristics
        visual_analysis = analysis_result.get('visual_analysis', {})
        script_indicators = visual_analysis.get('script_characteristics', {})
        
        if script_indicators.get('has_curved_strokes', False):
            relevance_score += 0.1
        if script_indicators.get('has_angular_shapes', False):
            relevance_score += 0.1
        
        return min(relevance_score, 1.0)
    
    def _extract_articles(self, text_content: str, analysis_result: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Extract potential wiki articles from the content"""
        articles = []
        
        # Split content into sections based on headers
        sections = self._split_into_sections(text_content)
        
        for section in sections:
            if len(section['content']) < self.min_content_length:
                continue
            
            # Create article structure
            article = {
                'title': section['title'] or 'Untitled Section',
                'content': section['content'],
                'summary': self._generate_summary(section['content']),
                'source': 'user_upload',
                'metadata': {
                    'extraction_source': analysis_result.get('file_info', {}).get('filename'),
                    'uploaded_by': user_id,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'confidence_score': section.get('confidence', 0.5)
                },
                'tags': self._extract_tags(section['content']),
                'difficulty_level': self._assess_difficulty(section['content']),
                'baybayin_examples': self._extract_baybayin_examples(section['content'])
            }
            
            articles.append(article)
        
        return articles
    
    def _extract_glossary_terms(self, text_content: str, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract potential glossary terms from the content"""
        terms = []
        
        # Look for definition patterns
        definition_patterns = [
            r'(\w+)\s*(?:is|means|refers to|defined as)\s*(.+?)(?:\.|$)',
            r'(\w+):\s*(.+?)(?:\n|$)',
            r'(\w+)\s*-\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) > 2 and len(definition) > 10:
                    terms.append({
                        'term': term,
                        'definition': definition,
                        'source': 'user_upload',
                        'baybayin_script': self._try_transliterate(term),
                        'metadata': {
                            'extraction_source': analysis_result.get('file_info', {}).get('filename'),
                            'confidence': 0.7
                        }
                    })
        
        return terms
    
    def _extract_timeline_events(self, text_content: str, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract historical timeline events from the content"""
        events = []
        
        # Look for year patterns and associated events
        year_patterns = [
            r'(?:in\s+)?(\d{3,4})(?:\s*(?:CE|AD|BC)?)[\s:,-]+(.+?)(?:\.|$)',
            r'(\d{1,2}(?:st|nd|rd|th)\s+century)[\s:,-]+(.+?)(?:\.|$)'
        ]
        
        for pattern in year_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                year_info = match.group(1).strip()
                description = match.group(2).strip()
                
                if len(description) > 20:
                    # Try to extract numeric year
                    year = self._extract_year(year_info)
                    
                    events.append({
                        'title': description[:100] + '...' if len(description) > 100 else description,
                        'year': year,
                        'period': year_info,
                        'description': description,
                        'source': 'user_upload',
                        'importance': 'medium',
                        'metadata': {
                            'extraction_source': analysis_result.get('file_info', {}).get('filename'),
                            'confidence': 0.6
                        }
                    })
        
        return events
    
    def _split_into_sections(self, text_content: str) -> List[Dict[str, Any]]:
        """Split content into logical sections"""
        sections = []
        
        # Simple section splitting based on headers
        lines = text_content.split('\n')
        current_section = {'title': None, 'content': '', 'confidence': 0.5}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a header
            if self._is_likely_header(line):
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line,
                    'content': '',
                    'confidence': 0.7
                }
            else:
                current_section['content'] += f"{line}\n"
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _is_likely_header(self, line: str) -> bool:
        """Determine if a line is likely a section header"""
        # Simple heuristics for header detection
        if len(line) > 100:  # Too long to be a header
            return False
        
        if line.isupper():  # All caps
            return True
        
        if line.startswith(('#', '##', '###')):  # Markdown headers
            return True
        
        if re.match(r'^\d+\.?\s+', line):  # Numbered sections
            return True
        
        # Check if line ends with colon
        if line.endswith(':'):
            return True
        
        return False
    
    def _generate_summary(self, content: str) -> str:
        """Generate a brief summary of the content"""
        sentences = content.split('.')
        # Take first few sentences as summary
        summary_sentences = sentences[:3]
        summary = '. '.join(sentence.strip() for sentence in summary_sentences if sentence.strip())
        
        # Limit length
        if len(summary) > 300:
            summary = summary[:297] + '...'
        
        return summary
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = []
        
        # Baybayin-related keywords
        baybayin_keywords = [
            'baybayin', 'alibata', 'script', 'writing', 'tagalog',
            'filipino', 'history', 'culture', 'pre-colonial'
        ]
        
        content_lower = content.lower()
        for keyword in baybayin_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        return list(set(tags))  # Remove duplicates
    
    def _assess_difficulty(self, content: str) -> str:
        """Assess the difficulty level of the content"""
        # Simple heuristics based on content complexity
        words = content.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        if avg_word_length > 7:
            return 'advanced'
        elif avg_word_length > 5:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _extract_baybayin_examples(self, content: str) -> List[Dict[str, str]]:
        """Extract Baybayin script examples from content"""
        examples = []
        
        # Look for Unicode Baybayin characters
        baybayin_matches = re.finditer(r'[\u1700-\u171F]+', content)
        for match in baybayin_matches:
            baybayin_text = match.group()
            # Try to find surrounding context
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].strip()
            
            examples.append({
                'baybayin': baybayin_text,
                'context': context,
                'transliteration': self._try_transliterate(baybayin_text)
            })
        
        return examples
    
    def _try_transliterate(self, text: str) -> str:
        """Attempt to transliterate text"""
        try:
            return self.transliteration_service.transliterate_text(text)
        except Exception:
            return ""
    
    def _analyze_content_structure(self, text_content: str) -> float:
        """Analyze structural elements in the content"""
        score = 0.0
        
        # Check for headers (simple heuristic)
        lines = text_content.split('\n')
        header_count = sum(1 for line in lines if self._is_likely_header(line))
        if header_count > 0:
            score += 0.3
        
        # Check for lists
        list_items = len(re.findall(r'^\s*[-*•]\s+', text_content, re.MULTILINE))
        if list_items > 0:
            score += 0.2
        
        # Check for paragraphs
        paragraphs = len([p for p in text_content.split('\n\n') if p.strip()])
        if paragraphs > 1:
            score += 0.3
        
        # Check for punctuation (indicates proper sentences)
        punctuation_count = len(re.findall(r'[.!?]', text_content))
        if punctuation_count > 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _analyze_language_quality(self, text_content: str) -> float:
        """Simple language quality analysis"""
        # This is a basic implementation - could be enhanced with NLP libraries
        score = 0.5  # Default score
        
        # Check word count
        words = text_content.split()
        if len(words) > 50:
            score += 0.2
        
        # Check for proper capitalization
        sentences = re.split(r'[.!?]+', text_content)
        capitalized_sentences = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        if capitalized_sentences > len(sentences) * 0.8:
            score += 0.3
        
        return min(score, 1.0)
    
    def _extract_year(self, year_info: str) -> int:
        """Extract numeric year from year information"""
        # Extract 4-digit year
        year_match = re.search(r'(\d{4})', year_info)
        if year_match:
            return int(year_match.group(1))
        
        # Extract 3-digit year (assume it's in the 1000s)
        year_match = re.search(r'(\d{3})', year_info)
        if year_match:
            return int(year_match.group(1))
        
        # Handle century notation
        century_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)\s+century', year_info.lower())
        if century_match:
            century = int(century_match.group(1))
            return (century - 1) * 100 + 50  # Middle of century
        
        return 0  # Default if no year found
