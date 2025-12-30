"""
AI Content Analyzer for Baybayin PDF Content
Automatically analyzes difficulty, categories, and prerequisites
"""

import os
import json
import logging
from typing import Dict, Any
from django.utils import timezone
from django.conf import settings

# For LLM integration - using your existing CHUTES API
import requests

logger = logging.getLogger(__name__)

class AIContentAnalyzer:
    """
    AI automatically analyzes PDF content for:
    - Difficulty level (0-1 scale)
    - Learning category 
    - Prerequisites
    - Cognitive complexity
    - Estimated study time
    """
    
    def __init__(self):
        self.api_key = os.environ.get("CHUTES_API_KEY")
        self.api_url = os.environ.get("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")
        
        if not self.api_key:
            logger.warning("CHUTES_API_KEY not found. AI analysis will use fallback values.")
    
    def analyze_content_difficulty(self, content: str) -> Dict[str, Any]:
        """
        AI automatically determines content characteristics for adaptive learning
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dict with difficulty score, category, prerequisites, etc.
        """
        
        if not self.api_key:
            return self._get_fallback_analysis(content)
        
        prompt = self._build_analysis_prompt(content)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in Baybayin script education and pedagogy. Analyze content for adaptive learning systems."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 512,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            content_response = response.json()["choices"][0]["message"]["content"]
            
            # Parse JSON response
            analysis = json.loads(content_response)
            
            # Validate and sanitize the response
            analysis = self._validate_analysis(analysis)
            
            logger.info(f"AI analyzed content: difficulty={analysis['difficulty_score']:.2f}, category={analysis['category']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._get_fallback_analysis(content)
    
    def _build_analysis_prompt(self, content: str) -> str:
        """Build the analysis prompt for the LLM"""
        
        # Truncate content if too long
        content = content[:1500] if len(content) > 1500 else content
        
        return f"""Analyze this Baybayin learning content for adaptive education system:

CONTENT TO ANALYZE:
{content}

Provide analysis in this EXACT JSON format:

{{
    "difficulty_score": 0.5,
    "category": "character_basics",
    "prerequisites": ["basic_reading"],
    "cognitive_level": "comprehension", 
    "estimated_study_minutes": 5,
    "reasoning": "Brief explanation"
}}

DIFFICULTY SCALE (0.0 to 1.0):
- 0.0-0.2: Basic character recognition, simple sounds, vowels
- 0.2-0.4: Vowel markers (kudlit), basic consonants, simple combinations  
- 0.4-0.6: Word formation, syllable construction, basic grammar
- 0.6-0.8: Complex words, advanced grammar rules, historical context
- 0.8-1.0: Advanced usage, cultural nuances, scholarly analysis

CATEGORIES (pick ONE most relevant):
- character_basics: Basic Baybayin characters and sounds
- vowel_system: Vowels, kudlit markers, diacritics
- consonant_system: Consonants, combinations
- word_formation: Building words, syllables
- grammar_rules: Writing rules, structure
- historical_context: History, origins, evolution  
- cultural_significance: Cultural meaning, traditions
- advanced_usage: Complex applications, scholarly topics

PREREQUISITES (concepts learner should know first):
- List 0-3 prerequisite concept names (or empty array if none)

COGNITIVE LEVELS:
- recognition: Just identify/recognize
- comprehension: Understand meaning  
- application: Use in context
- analysis: Compare/contrast/analyze
- synthesis: Create new understanding

Respond with ONLY the JSON object, no other text."""

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize AI analysis results"""
        
        # Set defaults for missing fields
        validated = {
            "difficulty_score": 0.5,
            "category": "general",
            "prerequisites": [],
            "cognitive_level": "comprehension", 
            "estimated_study_minutes": 5,
            "reasoning": "Auto-generated analysis"
        }
        
        # Validate difficulty score
        if "difficulty_score" in analysis:
            try:
                score = float(analysis["difficulty_score"])
                validated["difficulty_score"] = max(0.0, min(1.0, score))
            except (ValueError, TypeError):
                pass
        
        # Validate category
        valid_categories = [
            "character_basics", "vowel_system", "consonant_system", 
            "word_formation", "grammar_rules", "historical_context",
            "cultural_significance", "advanced_usage", "general"
        ]
        
        if analysis.get("category") in valid_categories:
            validated["category"] = analysis["category"]
        
        # Validate prerequisites
        if isinstance(analysis.get("prerequisites"), list):
            validated["prerequisites"] = analysis["prerequisites"][:5]  # Max 5
        
        # Validate cognitive level
        valid_levels = ["recognition", "comprehension", "application", "analysis", "synthesis"]
        if analysis.get("cognitive_level") in valid_levels:
            validated["cognitive_level"] = analysis["cognitive_level"]
        
        # Validate study time
        if "estimated_study_minutes" in analysis:
            try:
                minutes = int(analysis["estimated_study_minutes"])
                validated["estimated_study_minutes"] = max(1, min(60, minutes))
            except (ValueError, TypeError):
                pass
        
        # Keep reasoning if provided
        if isinstance(analysis.get("reasoning"), str):
            validated["reasoning"] = analysis["reasoning"][:500]  # Limit length
        
        return validated
    
    def _get_fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        
        # Simple heuristics for fallback
        content_lower = content.lower()
        
        # Estimate difficulty based on content characteristics
        difficulty = 0.5  # Default medium
        
        if any(word in content_lower for word in ['basic', 'simple', 'introduction', 'begin']):
            difficulty = 0.3
        elif any(word in content_lower for word in ['advanced', 'complex', 'history', 'cultural']):
            difficulty = 0.7
        elif any(word in content_lower for word in ['kudlit', 'diacritic', 'mark']):
            difficulty = 0.4
        
        # Estimate category
        category = "general"
        if any(word in content_lower for word in ['character', 'letter', 'symbol']):
            category = "character_basics"
        elif any(word in content_lower for word in ['vowel', 'kudlit', 'diacritic']):
            category = "vowel_system"
        elif any(word in content_lower for word in ['word', 'syllable', 'form']):
            category = "word_formation"
        elif any(word in content_lower for word in ['history', 'historical', 'origin']):
            category = "historical_context"
        
        return {
            "difficulty_score": difficulty,
            "category": category,
            "prerequisites": [],
            "cognitive_level": "comprehension",
            "estimated_study_minutes": 5,
            "reasoning": "Fallback analysis (AI unavailable)"
        }
    
    def batch_analyze_all_content(self) -> int:
        """
        Automatically analyze ALL PDF entries and update their AI metadata
        
        Returns:
            int: Number of entries processed
        """
        from baybayin_codex_pdf.models import PDFCodexEntry
        
        # Get unanalyzed entries
        pdf_entries = PDFCodexEntry.objects.filter(
            ai_difficulty_score__isnull=True
        )
        
        total = pdf_entries.count()
        processed = 0
        
        logger.info(f"Starting AI analysis of {total} PDF entries...")
        
        for entry in pdf_entries:
            try:
                # Analyze content
                analysis = self.analyze_content_difficulty(entry.cleaned_text or entry.text)
                
                # Update entry with AI analysis
                entry.ai_difficulty_score = analysis['difficulty_score']
                entry.ai_category = analysis['category']
                entry.ai_prerequisites = analysis['prerequisites']
                entry.ai_cognitive_level = analysis['cognitive_level']
                entry.ai_estimated_minutes = analysis['estimated_study_minutes']
                entry.ai_analysis_reasoning = analysis['reasoning']
                entry.ai_analyzed_at = timezone.now()
                entry.save()
                
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"Analyzed {processed}/{total} entries...")
                    
            except Exception as e:
                logger.error(f"Failed to analyze entry {entry.id}: {e}")
                continue
        
        logger.info(f"AI analysis complete: {processed}/{total} entries processed")
        return processed
    
    def reanalyze_entry(self, entry_id: int) -> bool:
        """
        Reanalyze a specific PDF entry
        
        Args:
            entry_id: ID of PDFCodexEntry to reanalyze
            
        Returns:
            bool: True if successful
        """
        from baybayin_codex_pdf.models import PDFCodexEntry
        
        try:
            entry = PDFCodexEntry.objects.get(id=entry_id)
            analysis = self.analyze_content_difficulty(entry.cleaned_text or entry.text)
            
            # Update entry
            entry.ai_difficulty_score = analysis['difficulty_score']
            entry.ai_category = analysis['category']
            entry.ai_prerequisites = analysis['prerequisites']
            entry.ai_cognitive_level = analysis['cognitive_level']
            entry.ai_estimated_minutes = analysis['estimated_study_minutes']
            entry.ai_analysis_reasoning = analysis['reasoning']
            entry.ai_analyzed_at = timezone.now()
            entry.save()
            
            logger.info(f"Reanalyzed entry {entry_id}: {analysis}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reanalyze entry {entry_id}: {e}")
            return False
