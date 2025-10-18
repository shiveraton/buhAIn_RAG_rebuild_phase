import re
from .constants import SUBSTITUTIONS
from text_transliteration.preprocessing.constants import BAYBAYIN_UNICODE_RANGE

def remove_special_characters(text):
    pattern = fr'[^a-z{BAYBAYIN_UNICODE_RANGE}\s]'
    removed_char = re.findall(pattern, text)
    new_text = re.sub(pattern, "", text)
    return new_text, removed_char

def substitute_foreign_letters_to_native(text):
    replaced = []
    
    for foreign_letter, native_letter in SUBSTITUTIONS.items():
        if foreign_letter in text:
            replaced.append(f"{foreign_letter} -> {native_letter}")
        text = text.replace(foreign_letter, native_letter)
    
    return text, replaced 