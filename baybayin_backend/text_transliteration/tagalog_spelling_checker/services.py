import os
from .checker import TagalogSpellingChecker
from text_transliteration.preprocessing.normalization_pipeline import text_transliteration_normalization

def spelling_check_pipeline(word):
    # Normalize the input word using the existing normalization function
    normalized_word, warnings = text_transliteration_normalization(word, transliterate=None)
    dict_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "dictionary",
        "tagalog_dictionary.txt"
    )

    # Defensive: ensure dictionary file exists
    if not os.path.exists(dict_path):
        return {
            "error": "dictionary_not_found",
            "message": f"Tagalog dictionary file not found at path: {dict_path}",
            "path": dict_path,
            "warnings": warnings
        }

    try:
        checker = TagalogSpellingChecker(dict_path, use_online=True)
        result = checker.check_text(normalized_word)
        result["warnings"] = warnings
        return result
    except Exception as e:
        # Return structured error instead of raising (so the view can return an informative JSON)
        return {
            "error": "checker_initialization_failed",
            "message": str(e),
            "path": dict_path,
            "warnings": warnings
        }

def spelling_stats():
    dict_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "dictionary",
        "tagalog_dictionary.txt"
    )
    if not os.path.exists(dict_path):
        return {"error": "dictionary_not_found", "path": dict_path}
    checker = TagalogSpellingChecker(dict_path, use_online=True)
    return checker.get_stats()