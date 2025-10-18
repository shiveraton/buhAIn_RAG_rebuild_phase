import re
import logging

logger = logging.getLogger(__name__)

def get_dependencies():
    """Get required dependencies for dictionary-based translation"""
    try:
        from ..transliterator import transliterate_latin_to_baybayin
        from preprocessing.normalization_pipeline import text_transliteration_normalization
        from .neural_translation import translate_en_to_tl
        return {
            'transliterator': transliterate_latin_to_baybayin,
            'translator': translate_en_to_tl,
            'normalizer': text_transliteration_normalization,
            'translation_method': 'neural'
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

        # step 1.5: run Tagalog spelling checker (if available) and prefer the corrected text for downstream normalization
        spell_checked_text = tagalog_text
        spelling_metadata = None
        try:
            from ..tagalog_spelling_checker.services import spelling_check_pipeline
            spell_res = spelling_check_pipeline(tagalog_text)
            # If the checker returned a structured result, derive a corrected phrase
            if isinstance(spell_res, dict) and not spell_res.get('error'):
                spelling_metadata = spell_res
                # If phrase-level suggestions are provided, use the first suggestion
                if not spell_res.get('is_correct', True):
                    if spell_res.get('suggestions'):
                        spell_checked_text = spell_res['suggestions'][0]
                    else:
                        # build per-word corrected phrase from results
                        parts = []
                        for r in spell_res.get('results', []):
                            if r.get('correct'):
                                parts.append(r.get('word'))
                            else:
                                s = r.get('suggestions')
                                if s:
                                    parts.append(s[0])
                                else:
                                    parts.append(r.get('word'))
                        if parts:
                            spell_checked_text = ' '.join(parts)
                steps.append(f"Spell-check: '{tagalog_text}' → '{spell_checked_text}'")
            else:
                # Spell-checker returned an error structure
                steps.append(f"Spell-check unavailable or failed: {getattr(spell_res, 'get', lambda k, d=None: None)('message')}")
        except Exception as e:
            logger.debug(f"Spelling checker import/execute failed: {e}")
            steps.append(f"Spell-check skipped: {str(e)}")

        # step 2: normalize the tagalog text for transliteration (use spell-checked text)
        normalized_text, warnings = deps['normalizer'](
            spell_checked_text, "to_baybayin"
        )
        steps.append(f"Normalization: '{spell_checked_text}' → '{normalized_text}'")
        
        #step 3: transliterate to baybayin
        baybayin_output = deps['transliterator'](normalized_text)
        steps.append(f"Tagalog → Baybayin: '{normalized_text}' → '{baybayin_output}'")
        
        result = {
            'original_text': text,
            'translated_text': tagalog_text,
            'spell_checked_text': spell_checked_text,
            'spelling_metadata': spelling_metadata,
            'normalized_text': normalized_text,
            'baybayin_text': baybayin_output,
            'steps': steps,
            'warnings': warnings,
            'translation_method': translation_method
        }

        return result
        
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
