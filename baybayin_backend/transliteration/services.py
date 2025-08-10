from preprocessing.normalization_pipeline import text_transliteration_normalization
from .transliterator import transliterate_latin_to_baybayin, transliterate_baybayin_to_latin

def text_transliteration_pipeline(text, transliteration_direction, source_language=None):
    """
    Main transliteration pipeline with support for cross-language transliteration.
    
    Args:
        text: Input text to transliterate
        transliteration_direction: "to_baybayin", "to_latin", or "cross_en_to_baybayin"
        source_language: Optional source language specification (for future expansion)
    """
    result = {}
    warnings = []
    
    if transliteration_direction == "cross_en_to_baybayin":
        try:
            from .cross_language.cross_transliterator import cross_transliterate_en_to_baybayin
            cross_result = cross_transliterate_en_to_baybayin(text, source_language or 'en')
            result.update(cross_result)
            if 'warnings' in cross_result:
                warnings.extend(cross_result['warnings'])
            return result, warnings
        except ImportError:
            result['error'] = 'Cross-language transliteration not available. Please install: pip install OpenNMT-py torch'
            return result, warnings
    
    normalized_text, norm_warnings = text_transliteration_normalization(text, transliteration_direction)
    result['normalized_text'] = normalized_text
    warnings.extend(norm_warnings)
    
    if transliteration_direction == "to_baybayin":
        transliterated_text = transliterate_latin_to_baybayin(normalized_text)
    elif transliteration_direction == "to_latin":
        transliterated_text = transliterate_baybayin_to_latin(normalized_text)
    else:
        raise ValueError(f"Unsupported transliteration direction: {transliteration_direction}")
    
    result['transliterated_text'] = transliterated_text
    
    return result, warnings
