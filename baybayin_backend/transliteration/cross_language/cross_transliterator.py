import re
import logging

logger = logging.getLogger(__name__)

def get_dependencies():
    """Get required dependencies with error handling"""
    try:
        from ..transliterator import transliterate_latin_to_baybayin
        from preprocessing.normalization_pipeline import text_transliteration_normalization
        from .translation_en_to_tl import translate_en_to_tl, is_translation_available
        
        if not is_translation_available():
            error_msg = "MarianMT model is not available. Please check your installation."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        return {
            'transliterator': transliterate_latin_to_baybayin,
            'translator': translate_en_to_tl,
            'normalizer': text_transliteration_normalization,
            'translation_method': 'ml'
        }
        
    except ImportError as e:
        logger.error(f"Failed to import core dependencies: {e}")
        return None

def normalize_text(text: str) -> str:
    """Optional: Strip punctuation, fix spacing, lowercase"""
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().lower()

def cross_transliterate_en_to_baybayin(text: str, source_language: str = 'en') -> dict:
    """
    Handles EN → TL → Baybayin transliteration.
    Returns a dictionary with intermediate steps for transparency.
    
    Args:
        text: The text to transliterate
        source_language: Source language code (default: 'en' for English)
    """
    source_language = 'en'
    
    if not text.strip():
        return {
            'original_text': text,
            'translated_text': '',
            'normalized_text': '',
            'baybayin_text': '',
            'steps': []
        }
    
    deps = get_dependencies()
    if not deps:
        return {
            'original_text': text,
            'translated_text': '',
            'normalized_text': '',
            'baybayin_text': '',
            'steps': [],
            'error': 'Cross-language transliteration dependencies not available.'
        }
    
    steps = []
    translation_method = deps.get('translation_method', 'unknown')
    
    try:
        # step 1: english to tagalog translation
        logger.info(f"Translating English text using {translation_method}: {text}")
        tagalog_text = deps['translator'](text)
        logger.info(f"Source language explicitly set to: English")
        
        if translation_method == 'ml':
            steps.append(f"English → Tagalog (AI): '{text}' → '{tagalog_text}'")
        else:
            steps.append(f"English → Tagalog (Dictionary): '{text}' → '{tagalog_text}'")
        
        # step 2: normalize the tagalog text for transliteration
        normalized_text, warnings = deps['normalizer'](
            tagalog_text, "to_baybayin"
        )
        steps.append(f"Normalization: '{tagalog_text}' → '{normalized_text}'")
        
        #step 3: transliterate to baybayin
        baybayin_output = deps['transliterator'](normalized_text)
        steps.append(f"Tagalog → Baybayin: '{normalized_text}' → '{baybayin_output}'")
        
        return {
            'original_text': text,
            'translated_text': tagalog_text,
            'normalized_text': normalized_text,
            'baybayin_text': baybayin_output,
            'steps': steps,
            'warnings': warnings,
            'translation_method': translation_method
        }
        
    except Exception as e:
        logger.error(f"Cross-transliteration failed: {str(e)}")
        return {
            'original_text': text,
            'translated_text': '',
            'normalized_text': '',
            'baybayin_text': '',
            'steps': steps,
            'error': str(e),
            'translation_method': translation_method
        }
