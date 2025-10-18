import re
from text_transliteration.constants import BAYBAYIN_UNICODE_RANGE

def remove_numbers(text):
    removed_num = re.findall(r'\d', text)
    new_text = re.sub(r'\d', "", text)

    return new_text, removed_num

# Used in Preprocessing and Transliteration
def is_baybayin_character(char):
    pattern = fr'[{BAYBAYIN_UNICODE_RANGE}]'
    return re.match(pattern, char) is not None

def is_vowel(c):
    return c.lower() in ['a', 'e', 'i', 'o', 'u'] is not None

def is_latin_alphabet(c):
    return re.match(r'[^a-z]', c) is not None