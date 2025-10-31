from text_transliteration.constants import LATIN_TO_BAYBAYIN
from text_transliteration.constants import LATIN_TO_BAYBAYIN_DIACRITICS, BAYBAYIN_VIRAMA
from text_transliteration.constants import BAYBAYIN_VOWELS, BAYBAYIN_CONSONANTS, BAYBAYIN_DIACRITICS
from text_transliteration.helper.regex_utils import is_vowel

def latin_to_baybayin_map(char, next_char=""):
    base = LATIN_TO_BAYBAYIN.get(char.lower(), "")
    if not is_vowel(char):
        if next_char in LATIN_TO_BAYBAYIN_DIACRITICS:
            return base + LATIN_TO_BAYBAYIN_DIACRITICS[next_char]
        elif next_char == "":
            return base + BAYBAYIN_VIRAMA
        else:
            return base
    else:
        return base
    
def baybayin_to_latin_map(current_char, diacritic=""):
    if current_char in BAYBAYIN_VOWELS:
        return BAYBAYIN_VOWELS[current_char]

    base = BAYBAYIN_CONSONANTS.get(current_char)
    if not base:
        return ""

    if diacritic in BAYBAYIN_DIACRITICS:
        return base + BAYBAYIN_DIACRITICS[diacritic]

    return base + "a"