import requests
import json
import os
from typing import Dict, List, Set
from .utils import _clean_word

class OnlineTagalogDictionary:
    """Simple online dictionary that fetches from GitHub-hosted Tagalog dictionary"""
    
    def __init__(self, cache_file='data/online_tagalog_cache.json'):
        self.cache_file = cache_file
        self.words_dict = {}
        self.words_set = set()
        self._load_or_fetch_dictionary()
    
    def _load_or_fetch_dictionary(self):
        """Load from cache or fetch from online source"""
        if os.path.exists(self.cache_file):
            try:
                print("Loading cached online dictionary...")
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'words' in data:
                        self.words_dict = data['words']
                        self.words_set = set(self.words_dict.keys())
                        print(f"Loaded {len(self.words_set)} words from cache")
                        return
            except Exception as e:
                print(f"Error loading cache: {e}")
        
        self._fetch_from_github()
    
    def _fetch_from_github(self):
        """Fetch dictionary from GitHub Pages"""
        print("Downloading Tagalog dictionary from online source...")
        
        try:
            url = "https://raymelon.github.io/tagalog-dictionary-scraper/tagalog_dict.json"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"Downloaded {len(data)} entries")
            
            processed_words = {}
            
            if isinstance(data, dict) and 'data' in data:
                # new format: {"data": ["word1", "word2", ...]}
                word_list = data['data']
                for word in word_list:
                    if isinstance(word, str):
                        clean_word = _clean_word(word)
                        if clean_word:
                            processed_words[clean_word] = ""
            elif isinstance(data, list):
                # if it's a list of words or objects
                for entry in data:
                    if isinstance(entry, str):
                        word = _clean_word(entry)
                        if word:
                            processed_words[word] = ""
                    elif isinstance(entry, dict) and 'word' in entry:
                        word = _clean_word(entry['word'])
                        if word:
                            definition = entry.get('definition', '').strip()
                            processed_words[word] = definition
            elif isinstance(data, dict):
                # if it's a dictionary (not with 'data' key)
                for key, value in data.items():
                    if key != 'data':
                        word = _clean_word(key)
                        if word:
                            processed_words[word] = str(value) if value else ""
            
            self.words_dict = processed_words
            self.words_set = set(processed_words.keys())
            
            # cache the results
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({'words': self.words_dict}, f, ensure_ascii=False, indent=2)
            
            print(f"Successfully processed {len(self.words_set)} unique words")
            
        except Exception as e:
            print(f"Could not download online dictionary: {e}")
            print("Falling back to local dictionary only")
            self.words_dict = {}
            self.words_set = set()
    
    def is_valid_word(self, word: str) -> bool:
        """Check if word exists in online dictionary"""
        return word.lower() in self.words_set
    
    def get_definition(self, word: str) -> str:
        """Get definition for a word"""
        return self.words_dict.get(word.lower(), "")
    
    def get_all_words(self) -> Set[str]:
        """Get all words from online dictionary"""
        return self.words_set.copy()
    
    def get_word_count(self) -> int:
        """Get total number of words"""
        return len(self.words_set)
