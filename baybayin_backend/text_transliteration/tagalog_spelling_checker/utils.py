import os
import re

def _clean_word(word: str) -> str:
    """
    Clean word by removing punctuation, numbers, and special characters.
    Preserves Tagalog-specific characters like ñ.
    """
    if not word:
        return ""
    
    # remove punctuation, numbers, and non-alphabetic characters
    # keep: a-z, A-Z, ñ, Ñ (common in Tagalog)
    cleaned = re.sub(r'[^a-zA-ZñÑ]', '', word.strip())
    return cleaned.lower()

def load_dictionary(dict_path):
    """
    Loads Tagalog words from a dictionary file. Assumes one word per line, optionally with frequency.
    Returns a set of words and a dict of word frequencies (if available).
    """
    words = set()
    frequencies = {}
    with open(dict_path, encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                word, freq = parts
                word = _clean_word(word)
                try:
                    freq_int = int(freq)
                except ValueError:
                    freq_int = 1  # Default frequency for non-integer values
                if word:
                    words.add(word)
                    frequencies[word] = freq_int
            elif len(parts) == 1:
                word = _clean_word(parts[0])
                if word:
                    words.add(word)
    return words, frequencies
