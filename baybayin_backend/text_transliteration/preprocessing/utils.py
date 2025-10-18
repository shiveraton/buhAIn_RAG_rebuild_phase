from .constants import BAYBAYIN_UNICODE_RANGE
import re

def is_latin_alphabet(c):
    return re.match(r'[^a-z]', c) is not None