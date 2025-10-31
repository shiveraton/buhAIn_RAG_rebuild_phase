from text_transliteration.preprocessing.normalization_pipeline import text_transliteration_normalization
from text_transliteration.transliterate.transliterate import transliterate_latin_to_baybayin, transliterate_baybayin_to_latin

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

    # Handle cross-language separately (uses its own pipeline)
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

    # Default spell-check variables
    spell_checked_text = None
    spelling_metadata = None

    # For Latin -> Baybayin, run Tagalog spelling checker on the input text before normalization
    if transliteration_direction == "to_baybayin":
        try:
            from .tagalog_spelling_checker.services import spelling_check_pipeline
            spell_res = spelling_check_pipeline(text)
            if isinstance(spell_res, dict) and not spell_res.get('error'):
                spelling_metadata = spell_res
                # Store the original text as the spell_checked_text initially
                # This ensures misspelled words are included in the output when no correction is applied
                spell_checked_text = text
                
                # Only provide suggested corrections in metadata for UI to display
                # The actual correction will only be applied if user explicitly selects it
                if not spell_res.get('is_correct', True):
                    # Keep original text with misspellings as the default output
                    # Suggestions are available in metadata for user to choose from
                    pass  # spell_checked_text remains as original input text
                else:
                    # Text is already correct
                    spell_checked_text = text
            else:
                # Spell-checker returned an error structure; include it in metadata
                spelling_metadata = spell_res
                spell_checked_text = text
        except Exception:
            # Spell checker unavailable - continue without it
            spell_checked_text = text
            spelling_metadata = None

    # Normalize (use spell-checked text when available for to_baybayin)
    text_to_normalize = spell_checked_text if spell_checked_text is not None else text
    normalized_text, norm_warnings = text_transliteration_normalization(text_to_normalize, transliteration_direction)
    result['normalized_text'] = normalized_text
    warnings.extend(norm_warnings)

    # Transliterate
    if transliteration_direction == "to_baybayin":
        transliterated_text = transliterate_latin_to_baybayin(normalized_text)
        # Attach spell-check metadata to result
        if spelling_metadata is not None:
            result['spell_checked_text'] = spell_checked_text
            result['spelling_metadata'] = spelling_metadata
    elif transliteration_direction == "to_latin":
        transliterated_text = transliterate_baybayin_to_latin(normalized_text)
        # After converting Baybayin -> Latin, run the spelling checker on the output to provide suggestions/metadata
        try:
            from .tagalog_spelling_checker.services import spelling_check_pipeline
            spell_res = spelling_check_pipeline(transliterated_text)
            if isinstance(spell_res, dict) and not spell_res.get('error'):
                # Keep original transliterated text (with potential misspellings) as the default output
                # Only provide suggestions in metadata for user to choose from
                result['spell_checked_text'] = transliterated_text
                result['spelling_metadata'] = spell_res
            else:
                # Checker returned error object
                result['spelling_metadata'] = spell_res
        except Exception:
            # Checker not available - skip
            pass
    else:
        raise ValueError(f"Unsupported transliteration direction: {transliteration_direction}")

    result['transliterated_text'] = transliterated_text

    return result, warnings


class TransliterationService:
    """
    Service class for Baybayin transliteration using the pipeline.
    """
    def __init__(self):
        pass

    def text_transliterate(self, text, direction, source_language=None):
        """
        Transliterate text using the pipeline.
        Args:
            text: Input text
            direction: 'to_baybayin', 'to_latin', or 'cross_en_to_baybayin'
            source_language: Optional source language
        Returns:
            result: dict with normalized and transliterated text
            warnings: list of warnings
        """
        return text_transliteration_pipeline(text, direction, source_language)
