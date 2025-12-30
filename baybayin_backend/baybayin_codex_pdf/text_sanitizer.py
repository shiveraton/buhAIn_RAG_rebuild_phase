"""
Comprehensive OCR Text Sanitation Pipeline for Baybayin Educational Content
Handles Filipino/Tagalog and English text cleaning for improved RAG quality
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class CleaningStats:
    """Statistics from the cleaning process"""
    original_length: int
    cleaned_length: int
    unicode_errors_fixed: int
    broken_words_merged: int
    hyphenation_fixed: int
    special_chars_removed: int
    confidence_score: float
    
class OCRTextSanitizer:
    """
    Comprehensive OCR text cleaning pipeline designed for Filipino/Tagalog and English
    educational content from scanned PDF books.
    """
    
    def __init__(self):
        self.setup_patterns()
        self.setup_dictionaries()
    
    def setup_patterns(self):
        """Initialize regex patterns for various OCR issues"""
        
        # Unicode garbage patterns - common OCR misreads
        self.unicode_garbage = re.compile(r'[^\w\s\-\'\"\.,\!\?\;\:\(\)\[\]\/\\\u00C0-\u017F\u1E00-\u1EFF]')
        
        # Broken word patterns - characters that break words incorrectly
        self.word_breakers = re.compile(r'(\w+)([|¡!1Il\]\[}{)(])(\w+)')
        
        # Hyphenation patterns - end of line hyphens that should be merged
        self.hyphen_pattern = re.compile(r'(\w+)-\s*\n\s*(\w+)', re.MULTILINE)
        
        # Multiple whitespace patterns
        self.multi_whitespace = re.compile(r'\s+')
        
        # Common OCR character misreads (Filipino/English context)
        self.char_corrections = {
            'rn': 'm',  # common OCR error
            'vv': 'w',  # common in older fonts
            '0': 'o',   # context-dependent
            '1': 'l',   # context-dependent
            '|': 'l',   # common vertical line misread
            '!': 'l',   # exclamation as lowercase l
            '][': 'h',  # brackets as h
            '}{': 'h',  # braces as h
            '()': 'o',  # parentheses as o
            '8': 'B',   # context-dependent
            '5': 'S',   # context-dependent
        }
        
        # Enhanced garbage patterns for aggressive cleaning
        self.severe_garbage_patterns = [
            re.compile(r'\b[A-Za-z]{1,2}[f\]\[\(\)\|\{\}]{1,3}[A-Za-z]{0,2}\b'),  # Mixed letters and symbols
            re.compile(r'\b[f\]\[\(\)\|\{\}]{2,}\b'),  # Pure symbol clusters
            re.compile(r'\b\w*[f\]\[\(\)\|\{\}]+\w*[f\]\[\(\)\|\{\}]+\w*\b'),  # Multiple symbol interruptions
            re.compile(r'\b[A-Za-z]+ ?[f\]\[\(\)\|\{\}]+ ?[A-Za-z]*\b'),  # Letter-symbol-letter patterns
            re.compile(r'\b[IlL1\|]{2,}\b'),  # Multiple similar vertical characters
            re.compile(r'\b\w{1,2} \w{1,2} \w{1,2}\b'),  # Very fragmented words
        ]
        
        # Filipino word patterns for better recognition
        self.filipino_corrections = {
            r'\bdo mate yo\b': 'doon sa',
            r'\bpila fo\b': 'pilipino',
            r'\biE Ror\b': '',  # garbage
            r'\barg aan ga\b': '',  # garbage
            r'\bcabeza de baanga\b': 'cabeza de barangay',
            r'\bsaisag\b': 'sagisag',
            r'\bmapupreng\b': 'maaaring',
            r'\bmapas slag\b': '',  # garbage
            r'\bpegs peas\b': '',  # garbage
        }
        
        # Filipino/Tagalog specific patterns
        self.tagalog_patterns = {
            # Common Filipino words that get OCR'd incorrectly
            r'\bsa\b': 'sa',  # preposition
            r'\bang\b': 'ang',  # article
            r'\bng\b': 'ng',   # particle
            r'\bna\b': 'na',   # particle/adjective marker
            r'\bmga\b': 'mga', # plural marker
            r'\bay\b': 'ay',   # copula
        }
        
        # English specific corrections
        self.english_patterns = {
            r'\bthe\b': 'the',
            r'\band\b': 'and',
            r'\bof\b': 'of',
            r'\bin\b': 'in',
            r'\bto\b': 'to',
        }
    
    def setup_dictionaries(self):
        """Setup common word dictionaries for validation"""
        
        # Common Filipino/Tagalog words (extend this based on your corpus)
        self.tagalog_words = {
            'ang', 'sa', 'ng', 'na', 'mga', 'ay', 'si', 'ni', 'kay', 'para',
            'nang', 'kung', 'hindi', 'oo', 'ako', 'ikaw', 'siya', 'kami', 'kayo', 'sila',
            'ito', 'iyan', 'iyon', 'dito', 'dyan', 'doon', 'sino', 'ano', 'saan', 'kailan',
            'paano', 'bakit', 'magkano', 'ilan', 'alin', 'baybayin', 'sulat', 'titik',
            'salita', 'wika', 'kultura', 'kasaysayan', 'pilipinas', 'tagalog', 'filipino',
            # Add more comprehensive Filipino words
            'kailangan', 'kailangang', 'umakma', 'likas', 'ibang', 'pamayanang', 'kultural',
            'naman', 'tulad', 'saysay', 'salaysay', 'tikas', 'mga', 'nito', 'kabeza', 'cabeza',
            'una', 'kasaysayan', 'pagan', 'basin', 'mapupren', 'mapas', 'mag', 'at'
        }
        
        # Common English words
        self.english_words = {
            'the', 'and', 'of', 'in', 'to', 'for', 'with', 'on', 'by', 'from',
            'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
        }
    
    def detect_language_regions(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect language regions in the text (Filipino vs English)
        Returns list of (start, end, language) tuples
        """
        words = text.split()
        regions = []
        current_lang = None
        start_pos = 0
        
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Skip very short words
            if len(clean_word) < 2:
                continue
                
            # Determine language of current word
            is_tagalog = clean_word in self.tagalog_words
            is_english = clean_word in self.english_words
            
            detected_lang = None
            if is_tagalog and not is_english:
                detected_lang = 'tl'
            elif is_english and not is_tagalog:
                detected_lang = 'en'
            elif is_tagalog and is_english:
                # Ambiguous - use context or default to tagalog
                detected_lang = 'tl'
            
            # Track language regions
            if detected_lang and detected_lang != current_lang:
                if current_lang is not None:
                    regions.append((start_pos, i, current_lang))
                current_lang = detected_lang
                start_pos = i
        
        # Add final region
        if current_lang is not None:
            regions.append((start_pos, len(words), current_lang))
        
        return regions
    
    def remove_severe_garbage(self, text: str) -> Tuple[str, int]:
        """Aggressively remove OCR garbage"""
        fixes = 0
        try:
            for i, pattern in enumerate(self.severe_garbage_patterns):
                logger.debug(f"Pattern {i}: {pattern}")
                before_count = len(pattern.findall(text))
                text = pattern.sub(' ', text)
                fixes += before_count
            for pattern, replacement in self.filipino_corrections.items():
                logger.debug(f"Filipino pattern: {pattern} -> {replacement}")
                before_matches = len(re.findall(pattern, text, re.IGNORECASE))
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                fixes += before_matches
        except Exception as e:
            import traceback
            logger.error(f"Error in remove_severe_garbage: {str(e)}")
            traceback.print_exc()
            raise
        return text, fixes

    def fix_filipino_specific_errors(self, text: str) -> Tuple[str, int]:
        """Fix Filipino/Tagalog specific OCR errors"""
        fixes = 0
        filipino_fixes = {
            r'\btikeas\b': 'tikas',
            r'\bsavsatiw\b': 'salaysay',
            r'\bkailangang\b': 'kailangan',
            r'\bumakma\b': 'umangkop',
        }
        for pattern, replacement in filipino_fixes.items():
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                fixes += matches
        return text, fixes
    
    def fix_unicode_errors(self, text: str) -> Tuple[str, int]:
        """Fix Unicode encoding errors and garbage characters"""
        fixes = 0
        
        # Normalize Unicode (NFD -> NFC)
        text = unicodedata.normalize('NFC', text)
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        fixes += len(re.findall(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', text))
        
        # Fix common Unicode misreads
        unicode_fixes = {
            'â€™': "'",  # smart quote
            'â€œ': '"',  # open quote
            'â€': '"',   # close quote
            'â€"': '—',  # em dash
            'â€"': '–',  # en dash
            'Ã¡': 'á',   # a with acute
            'Ã©': 'é',   # e with acute
            'Ã­': 'í',   # i with acute
            'Ã³': 'ó',   # o with acute
            'Ãº': 'ú',   # u with acute
            'Ã±': 'ñ',   # n with tilde
        }
        
        for bad, good in unicode_fixes.items():
            if bad in text:
                text = text.replace(bad, good)
                fixes += 1
        
        # Remove remaining Unicode garbage (but preserve Filipino diacritics)
        original_len = len(text)
        text = self.unicode_garbage.sub('', text)
        fixes += original_len - len(text)
        
        return text, fixes
    
    def fix_broken_words(self, text: str) -> Tuple[str, int]:
        """Fix words broken by OCR character recognition errors"""
        fixes = 0
        
        # Fix words broken by misread characters
        def fix_breaker(match):
            nonlocal fixes
            word1, breaker, word2 = match.groups()
            
            # Common cases where we should merge
            if len(word1) > 1 and len(word2) > 1:
                # If breaker looks like it should be a letter
                if breaker in '|1Il!':
                    fixes += 1
                    if word1.lower() + 'l' + word2.lower() in self.tagalog_words or \
                       word1.lower() + 'l' + word2.lower() in self.english_words:
                        return word1 + 'l' + word2
                    return word1 + word2
                elif breaker in '][}{':
                    fixes += 1
                    if word1.lower() + 'h' + word2.lower() in self.tagalog_words or \
                       word1.lower() + 'h' + word2.lower() in self.english_words:
                        return word1 + 'h' + word2
                    return word1 + word2
            
            return match.group(0)  # No change
        
        text = self.word_breakers.sub(fix_breaker, text)
        
        return text, fixes
    
    def fix_hyphenation(self, text: str) -> Tuple[str, int]:
        """Fix hyphenation at line breaks"""
        fixes = 0
        
        def merge_hyphen(match):
            nonlocal fixes
            word1, word2 = match.groups()
            # Merge if it creates a valid word
            merged = word1 + word2
            if len(merged) > 3:  # Reasonable word length
                fixes += 1
                return merged
            return match.group(0)
        
        text = self.hyphen_pattern.sub(merge_hyphen, text)
        return text, fixes
    
    def fix_character_misreads(self, text: str) -> Tuple[str, int]:
        """Fix common OCR character misreads using context"""
        fixes = 0
        words = text.split()
        corrected_words = []
        
        for word in words:
            original_word = word
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Skip very short words
            if len(clean_word) < 2:
                corrected_words.append(word)
                continue
            
            # Try character corrections if word is not in dictionaries
            if clean_word not in self.tagalog_words and clean_word not in self.english_words:
                best_correction = None
                best_score = 0
                
                # Try each character correction
                for bad_char, good_char in self.char_corrections.items():
                    if bad_char in clean_word:
                        corrected = clean_word.replace(bad_char, good_char)
                        
                        # Score the correction
                        score = 0
                        if corrected in self.tagalog_words:
                            score = 2
                        elif corrected in self.english_words:
                            score = 1
                        
                        if score > best_score:
                            best_correction = corrected
                            best_score = score
                
                # Apply best correction
                if best_correction and best_score > 0:
                    # Preserve original casing and punctuation
                    corrected_word = word
                    for bad_char, good_char in self.char_corrections.items():
                        corrected_word = corrected_word.replace(bad_char, good_char)
                        corrected_word = corrected_word.replace(bad_char.upper(), good_char.upper())
                    
                    corrected_words.append(corrected_word)
                    if corrected_word.lower() != original_word.lower():
                        fixes += 1
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), fixes
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks"""
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Fix multiple spaces
        text = self.multi_whitespace.sub(' ', text)
        
        # Clean up paragraph breaks (preserve meaningful ones)
        # Multiple newlines become double newline (paragraph break)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Single newlines become spaces (unless they're clearly paragraph breaks)
        lines = text.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                cleaned_lines.append('')
            else:
                # If line ends with sentence-ending punctuation, keep the line break
                if line.endswith(('.', '!', '?', ':')) or \
                   (i < len(lines) - 1 and lines[i + 1].strip() == ''):
                    cleaned_lines.append(line)
                else:
                    # Join with next line
                    cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Final cleanup
        text = re.sub(r' +', ' ', text)  # Multiple spaces
        text = text.strip()
        
        return text
    
    def calculate_confidence_score(self, original: str, cleaned: str, stats: CleaningStats) -> float:
        """
        Calculate confidence score for the cleaned text
        Higher score = more confident in the cleaning quality
        """
        
        # Base score
        score = 0.5
        
        # Length preservation (penalty for too much content loss)
        if stats.original_length > 0:
            length_ratio = stats.cleaned_length / stats.original_length
            if 0.7 <= length_ratio <= 1.1:  # Good length preservation
                score += 0.2
            elif length_ratio < 0.5:  # Too much content lost
                score -= 0.3
        
        # Fixes applied (moderate fixes are good, too many might indicate poor OCR)
        total_fixes = (stats.unicode_errors_fixed + stats.broken_words_merged + 
                      stats.hyphenation_fixed + stats.special_chars_removed)
        
        if total_fixes == 0:
            score += 0.1  # Clean text is good
        elif 1 <= total_fixes <= 10:
            score += 0.2  # Reasonable fixes
        elif total_fixes > 20:
            score -= 0.2  # Too many fixes might indicate poor quality
        
        # Word ratio (percentage of recognized words)
        cleaned_words = [w.strip().lower() for w in re.findall(r'\w+', cleaned)]
        if cleaned_words:
            known_words = sum(1 for w in cleaned_words 
                            if w in self.tagalog_words or w in self.english_words or len(w) == 1)
            word_ratio = known_words / len(cleaned_words)
            score += word_ratio * 0.3
        
        return min(1.0, max(0.0, score))
    
    def clean_ocr_text(self, raw_text: str) -> Tuple[str, CleaningStats]:
        """
        Main cleaning pipeline - processes raw OCR text through all cleaning steps
        
        Args:
            raw_text: Raw OCR output text
            
        Returns:
            Tuple of (cleaned_text, cleaning_statistics)
        """
        if not raw_text or not raw_text.strip():
            return "", CleaningStats(0, 0, 0, 0, 0, 0, 0.0)
        
        original_length = len(raw_text)
        text = raw_text
        
        # Track fixes
        unicode_fixes = 0
        broken_word_fixes = 0
        hyphen_fixes = 0
        char_fixes = 0
        
        logger.info(f"Starting OCR cleaning for text of length {original_length}")
        
        try:
            # Step 1: Remove severe garbage first
            logger.debug("Starting garbage removal")
            text, garbage_fixes = self.remove_severe_garbage(text)
            logger.debug(f"Garbage removed: {garbage_fixes}")
            
            # Step 2: Fix Filipino-specific errors
            logger.debug("Starting Filipino fixes")
            text, filipino_fixes = self.fix_filipino_specific_errors(text)
            logger.debug(f"Filipino fixes: {filipino_fixes}")
            
            # Step 3: Fix Unicode encoding errors
            text, unicode_fixes = self.fix_unicode_errors(text)
            logger.debug(f"Unicode fixes: {unicode_fixes}")
            
            # Step 4: Fix broken words
            text, broken_word_fixes = self.fix_broken_words(text)
            logger.debug(f"Broken word fixes: {broken_word_fixes}")
            
            # Step 5: Fix hyphenation
            text, hyphen_fixes = self.fix_hyphenation(text)
            logger.debug(f"Hyphenation fixes: {hyphen_fixes}")
            
            # Step 6: Fix character misreads
            text, char_fixes = self.fix_character_misreads(text)
            logger.debug(f"Character fixes: {char_fixes}")
            
            # Step 7: Normalize whitespace
            text = self.normalize_whitespace(text)
            
            # Create statistics
            stats = CleaningStats(
                original_length=original_length,
                cleaned_length=len(text),
                unicode_errors_fixed=unicode_fixes,
                broken_words_merged=broken_word_fixes,
                hyphenation_fixed=hyphen_fixes,
                special_chars_removed=char_fixes,
                confidence_score=0.0  # Will be calculated below
            )
            
            # Calculate confidence score
            stats.confidence_score = self.calculate_confidence_score(raw_text, text, stats)
            
            logger.info(f"OCR cleaning complete. Confidence: {stats.confidence_score:.2f}")
            
            return text, stats
            
        except Exception as e:
            logger.error(f"Error during OCR cleaning: {str(e)}")
            # Return original text with minimal stats if cleaning fails
            stats = CleaningStats(
                original_length=original_length,
                cleaned_length=original_length,
                unicode_errors_fixed=0,
                broken_words_merged=0,
                hyphenation_fixed=0,
                special_chars_removed=0,
                confidence_score=0.1  # Low confidence for failed cleaning
            )
            return raw_text, stats


# Convenience function for easy integration
def sanitize_ocr_text(raw_text: str) -> Tuple[str, Dict]:
    """
    Convenience function to clean OCR text and return results
    
    Args:
        raw_text: Raw OCR output
        
    Returns:
        Tuple of (cleaned_text, stats_dict)
    """
    sanitizer = OCRTextSanitizer()
    cleaned_text, stats = sanitizer.clean_ocr_text(raw_text)
    
    # Convert stats to dictionary for JSON serialization
    stats_dict = {
        'original_length': stats.original_length,
        'cleaned_length': stats.cleaned_length,
        'unicode_errors_fixed': stats.unicode_errors_fixed,
        'broken_words_merged': stats.broken_words_merged,
        'hyphenation_fixed': stats.hyphenation_fixed,
        'special_chars_removed': stats.special_chars_removed,
        'confidence_score': stats.confidence_score,
        'compression_ratio': stats.cleaned_length / max(1, stats.original_length),
        'total_fixes': (stats.unicode_errors_fixed + stats.broken_words_merged + 
                       stats.hyphenation_fixed + stats.special_chars_removed)
    }
    
    return cleaned_text, stats_dict
