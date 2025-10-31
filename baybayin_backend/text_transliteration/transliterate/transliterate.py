from text_transliteration.transliterate.mapping import latin_to_baybayin_map, baybayin_to_latin_map
from text_transliteration.constants import BAYBAYIN_VOWELS, BAYBAYIN_DIACRITICS, BAYBAYIN_CONSONANTS
from text_transliteration.helper.regex_utils import is_vowel, is_baybayin_character, is_latin_alphabet

def transliterate_latin_to_baybayin(text):
    i = 0
    baybayin = ""
    while i < len(text):
        char = text[i]
        if char == " " or is_baybayin_character(char):
            baybayin += char if is_baybayin_character(char) else " "
            i += 1
            continue
        elif char == "n" and i+1 < len(text) and text[i+1] == "g":
            i += 1
            char += text[i]
            if i + 1 < len(text):
                if is_vowel(text[i + 1]):
                    i += 1
                    next_char = text[i]
                elif not is_vowel(text[i+1]) and not is_latin_alphabet(text[i+1]):
                    print(text[i+1])
                    next_char = ""
                else:
                    next_char = text[i]
            else:
                next_char = ""
                i += 1
        elif i+1 < len(text) and not is_vowel(char) and is_vowel(text[i + 1]):
            i += 1
            next_char = text[i]
        else:
            next_char = ""
        result = latin_to_baybayin_map(char, next_char)
        baybayin += result
        i += 1
    return baybayin
def transliterate_baybayin_to_latin(text):
    i = 0
    latin = ""
    while i<len(text):
        char = text[i]
        if char == " " or not is_baybayin_character(char):
            latin += char
            i += 1
            continue
        elif i+1 < len(text) and char not in BAYBAYIN_VOWELS:
            if text[i+1] in BAYBAYIN_DIACRITICS:
                i += 1
                next_char = text[i]
            elif text[i+1] not in BAYBAYIN_DIACRITICS:
                next_char = ""
        else:
            next_char = ""
            
        result = baybayin_to_latin_map(char, next_char)
        latin += result
        i += 1

    return latin