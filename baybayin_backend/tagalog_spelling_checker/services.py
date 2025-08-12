import os
from .checker import TagalogSpellingChecker
from preprocessing.normalization_pipeline import text_transliteration_normalization

def spelling_check_pipeline(word):
    # Normalize the input word using the existing normalization function
    normalized_word, warnings = text_transliteration_normalization(word, transliterate=None)
    dict_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "dictionary",
        "tagalog_dictionary.txt"
    )
    checker = TagalogSpellingChecker(dict_path, use_online=True)
    result = checker.check_text(normalized_word)
    result["warnings"] = warnings
    return result

def spelling_stats():
    dict_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "dictionary",
        "tagalog_dictionary.txt"
    )
    checker = TagalogSpellingChecker(dict_path, use_online=True)
    return checker.get_stats()