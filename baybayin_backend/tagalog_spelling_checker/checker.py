from .utils import load_dictionary
from rapidfuzz import process, fuzz
import os
import re
from collections import Counter

class TagalogSpellingChecker:
    def __init__(self, dict_path, use_online=False):
        """
        Initialize the spelling checker.
        
        Args:
            dict_path: Path to local dictionary file
            use_online: Whether to also use online dictionary (default: False for backward compatibility)
        """
        # load local dictionary
        self.words, self.frequencies = load_dictionary(dict_path)
        self.local_words = self.words.copy()
        
        # online
        self.online_dict = None
        self.online_words = set()
        
        if use_online:
            try:
                from .online_dictionary import OnlineTagalogDictionary
                self.online_dict = OnlineTagalogDictionary()
                self.online_words = self.online_dict.get_all_words()
                
                # combine both 
                self.words = self.words.union(self.online_words)
                
                # create enhanced frequencies for online words
                self._enhance_frequencies()
                
                print(f"Checker initialized with {len(self.local_words)} local + {len(self.online_words)} online = {len(self.words)} total words")
                
            except ImportError:
                print("Online dictionary not available, using local only")
            except Exception as e:
                print(f"Could not load online dictionary: {e}")
                print("Falling back to local dictionary only")

    def _enhance_frequencies(self):
        """Add estimated frequencies for online-only words"""
        for word in self.online_words:
            if word not in self.frequencies:
                base_freq = 500  #base frequency for online words
                
                # boost for shorter, more common words
                if len(word) <= 4:
                    base_freq += 500
                elif len(word) <= 6:
                    base_freq += 200
                
                # boost for common patterns
                common_patterns = ['ang', 'mga', 'sa', 'ng', 'na', 'ay', 'mag', 'pag', 'ka']
                for pattern in common_patterns:
                    if pattern in word:
                        base_freq += 300
                        break
                
                self.frequencies[word] = base_freq

    def is_correct(self, word):
        """Check if word is correct in local or online dictionary"""
        return word in self.words

    def suggest(self, word, limit=3, score_cutoff=70):
        """Enhanced suggestion system that differentiates between real typos and intentional scrambling"""
        
        # first check if the word is already correct
        if self.is_correct(word):
            return []
        
        # then check if this might be intentional scrambling or a foreign word
        suggestion_type = self._analyze_word_type(word)
        
        if suggestion_type == "scrambled":
            # for intentionally scrambled words, return no suggestions or a special message
            return []
        elif suggestion_type == "foreign":
            # for foreign words/names, return no suggestions
            return []
        elif suggestion_type == "typo":
            # for real typos, use enhanced matching
            return self._get_typo_suggestions(word, limit, score_cutoff)
        else:
            # default behavior for unclear cases
            return self._get_typo_suggestions(word, limit, score_cutoff)
    
    def _analyze_word_type(self, word):
        """Analyze if a word is a real typo, intentional scrambling, or foreign word"""
        
        # handle edge cases first
        if len(word) == 0:
            return "foreign"
        if len(word) == 1:
            return "typo"  # single letters are likely typos
        
        # Rule 1: Check for foreign words/names first (most restrictive)
        if self._is_likely_foreign(word):
            return "foreign"
        
        # Rule 2: Check for intentional scrambling (specific patterns)
        if self._is_definitely_scrambled(word):
            return "scrambled"
        
        # Rule 3: Default to typo for everything else
        return "typo"
    
    def _is_definitely_scrambled(self, word):
        """Detect clear cases of intentional scrambling"""
        
        #specific patterns for words related to "babae" (the main case we're handling)
        if self._is_babae_scrambling(word):
            return True
        
        #general scrambling detection for other cases
        best_matches = process.extract(
            word, self.words, scorer=fuzz.ratio, limit=15, score_cutoff=60
        )
        
        # sort by score descending to prioritize closer matches
        best_matches = sorted(best_matches, key=lambda x: x[1], reverse=True)
        
        # priority check: look for common/important words first
        common_important_words = {
            'babae', 'lalaki', 'tao', 'anak', 'pamilya', 'bahay', 'tubig', 
            'araw', 'gabi', 'buwan', 'taon', 'oras', 'mabuti', 'masama', 'malaki', 
            'maliit', 'kumain', 'uminom', 'matulog', 'maganda', 'pangit'
        }
        
        # first pass: check high-scoring anagrams of important words
        for match, score, _ in best_matches:
            if (self._is_anagram(word, match) and 
                match.lower() in common_important_words and 
                score >= 80):
                # for important word anagrams, be more conservative
                if self._has_strong_scrambling_evidence(word, match):
                    return True
                else:
                    # if an important word doesn't show strong scrambling, it's likely a typo
                    return False
        
        # second pass: general anagram detection for other words
        for match, score, _ in best_matches:
            if self._is_anagram(word, match):
                # skip important words (already checked above)
                if match.lower() in common_important_words:
                    continue
                    
                # for non-important words, use regular logic
                if score >= 80:
                    if self._has_strong_scrambling_evidence(word, match):
                        return True
                else:
                    if self._has_clear_scrambling_pattern(word, match):
                        return True
        
        return False
    
    def _is_babae_scrambling(self, word):
        """Detect scrambling specifically related to 'babae' and similar common words"""
        
        #check if word is an anagram of common target words
        common_targets = ['babae', 'lalaki', 'tao', 'maganda', 'mabait']
        
        for target in common_targets:
            if target in self.words and self._is_anagram(word, target):
                #check if this looks like intentional scrambling vs typo
                different_positions = sum(1 for a, b in zip(word, target) if a != b)
                
                #special case for "babae" variants
                if target == 'babae':
                    # "babai" vs "babae" - only 1 position different, likely typo
                    if different_positions <= 2:
                        return False
                    # "ababe", "baeba", "beaba" vs "babae" - 3+ positions different, likely scrambling
                    else:
                        return True
                
                # Special case for "lalaki" variants  
                elif target == 'lalaki':
                    # "lalkai" vs "lalaki" - only 2 adjacent swaps, likely typo
                    if different_positions <= 2:
                        return False
                    # More significant scrambling
                    else:
                        return True
                
                # For other words, use general rule (require 3+ different positions)
                if different_positions >= 3:
                    return True
        
        return False
    
    def _has_clear_scrambling_pattern(self, word, target):
        """Check if word has clear scrambling patterns relative to target"""
        
        # Must be same length
        if len(word) != len(target):
            return False
        
        # Must have substantial rearrangement (3+ different positions)
        different_positions = sum(1 for a, b in zip(word, target) if a != b)
        if different_positions < 3:
            return False
        
        # Target should be significantly more common or be in our important words list
        target_freq = self.frequencies.get(target, 0)
        important_words = self._get_common_words()
        
        # Only consider it scrambling if:
        # 1. Target is in our important words list, OR
        # 2. Target has substantially higher frequency (>5), OR  
        # 3. Target frequency is >2 AND it looks more natural than input
        if (target in important_words or 
            target_freq > 5 or
            (target_freq > 2 and self._looks_more_natural_simple(target, word))):
            return True
        
        return False
    
    def _is_meaningful_scrambling(self, word, target):
        """Check if this looks like intentional scrambling rather than a typo"""
        
        # Rule 1: Target word should be reasonably common or important
        target_freq = self.frequencies.get(target, 0)
        is_common = target in self._get_common_words() or target_freq > 0
        
        if not is_common:
            return False
        
        # Rule 2: Check for patterns that suggest intentional scrambling
        # Look for repetitive patterns in the scrambled word
        word_has_repetition = self._has_repetitive_pattern_simple(word)
        target_has_repetition = self._has_repetitive_pattern_simple(target)
        
        # If the input has repetitive patterns but target doesn't, likely scrambling
        if word_has_repetition and not target_has_repetition:
            return True
        
        # Rule 3: Target should be "more natural" looking than input
        # This helps distinguish "ababe"→"babae" (scrambling) from "babai"→"ibaba" (typo)
        if self._looks_more_natural_simple(target, word):
            return True
        
        return False
    
    def _has_repetitive_pattern_simple(self, word):
        """Simple check for repetitive patterns in a word"""
        # Look for repeated substrings of length 2+
        for i in range(len(word) - 1):
            for j in range(i + 2, min(i + 4, len(word) + 1)):  # Check substrings of length 2-3
                substring = word[i:j]
                if word.count(substring) > 1:
                    return True
        return False
    
    def _looks_more_natural_simple(self, word1, word2):
        """Simple heuristic: word1 looks more natural than word2"""
        
        # Check if word1 has better vowel distribution
        vowels = 'aeiou'
        
        def has_good_vowel_pattern(w):
            vowel_count = sum(1 for c in w.lower() if c in vowels)
            # Good words typically have 40-60% vowels
            vowel_ratio = vowel_count / len(w) if len(w) > 0 else 0
            return 0.3 <= vowel_ratio <= 0.7
        
        word1_good = has_good_vowel_pattern(word1)
        word2_good = has_good_vowel_pattern(word2)
        
        # If one has good pattern and other doesn't, prefer the good one
        if word1_good and not word2_good:
            return True
        if word2_good and not word1_good:
            return False
        
        # Check for alternating vowel-consonant patterns (more natural)
        def vowel_consonant_alternation_score(w):
            score = 0
            for i in range(len(w) - 1):
                curr_vowel = w[i].lower() in vowels
                next_vowel = w[i + 1].lower() in vowels
                if curr_vowel != next_vowel:  # Alternating
                    score += 1
            return score
        
        return vowel_consonant_alternation_score(word1) > vowel_consonant_alternation_score(word2)
    
    def _get_common_words(self):
        """Get a set of common/important Tagalog words"""
        return {
            'babae', 'lalaki', 'tao', 'anak', 'pamilya', 'bahay', 'gulo', 'tubig', 
            'araw', 'gabi', 'buwan', 'taon', 'oras', 'mabuti', 'masama', 'malaki', 
            'maliit', 'kumain', 'uminom', 'matulog', 'maganda', 'pangit', 'mga',
            'ang', 'sa', 'ng', 'na', 'ay', 'at', 'para', 'hindi', 'ako', 'ka',
            'siya', 'kami', 'kayo', 'sila', 'ito', 'iyan', 'iyon'
        }
    
    def _is_substantial_rearrangement(self, word, original):
        """Check if word is a substantial rearrangement of original (not a simple typo)"""
        
        if len(word) != len(original):
            return False
        
        # Count positions where characters differ
        different_positions = sum(1 for a, b in zip(word, original) if a != b)
        
        # For short words (5 chars or less), need at least 3 different positions
        if len(word) <= 5:
            return different_positions >= 3
        
        # For longer words, need at least half the positions to be different
        return different_positions >= len(word) // 2
    
    def _is_likely_scrambled_enhanced(self, word):
        """Enhanced detection for intentionally scrambled words"""
        
        # Get the best overall matches first
        best_matches = process.extract(
            word, self.words, scorer=fuzz.ratio, limit=15, score_cutoff=30
        )
        
        # Look for potential scrambling patterns
        for match, score, _ in best_matches:
            # Check if this could be intentional scrambling
            if self._is_likely_scrambling_pattern(word, match, score):
                return True
        
        return False
    
    def _is_likely_scrambling_pattern(self, word, candidate, score):
        """Check if the relationship between word and candidate suggests intentional scrambling"""
        
        # Skip if lengths are very different
        if abs(len(word) - len(candidate)) > 2:
            return False
        
        # Skip if the score is too low (not similar enough to be scrambling)
        if score < 50:
            return False
        
        # Check for scrambling indicators:
        
        # 1. Same or very similar character composition (anagrams or near-anagrams)
        word_chars = sorted(word.lower())
        candidate_chars = sorted(candidate.lower())
        
        if word_chars == candidate_chars:  # Perfect anagram
            # For anagrams, check if the pattern suggests intentional scrambling vs typo
            if self._is_intentional_scrambling(word, candidate):
                # Additional check: candidate should be a meaningful word
                # (in dictionary and not extremely rare)
                candidate_freq = self.frequencies.get(candidate, 0)
                if candidate_freq > 0:  # Just needs to be in dictionary
                    return True
        
        # 2. High character overlap with significant rearrangement
        if len(word) == len(candidate):
            common_chars = set(word.lower()) & set(candidate.lower())
            overlap_ratio = len(common_chars) / len(set(word.lower()))
            
            if overlap_ratio > 0.7 and score > 60:  # High overlap but not too similar
                # Check if it's a complex rearrangement
                different_positions = sum(1 for a, b in zip(word, candidate) if a != b)
                if different_positions >= len(word) // 2:  # Many positions different
                    candidate_freq = self.frequencies.get(candidate, 0)
                    if candidate_freq > 0:  # Just needs to be in dictionary
                        return True
        
        # 3. Detection for specific patterns like "ababe" from "babae"
        if self._is_repetition_scrambling(word, candidate):
            return True
        
        return False
    
    def _is_repetition_scrambling(self, word, candidate):
        """Detect scrambling that involves character repetition patterns"""
        
        # Look for patterns where parts of the word are repeated/rearranged
        # e.g., "ababe" from "babae" (taking "a", then "ba", then "be")
        
        if len(word) != len(candidate):
            return False
        
        # Check if candidate is in dictionary (any frequency is fine)
        candidate_freq = self.frequencies.get(candidate, 0)
        if candidate_freq == 0:  # Not in dictionary
            return False
        
        # Look for repetitive substrings in the input word
        has_repetition = False
        for i in range(len(word) - 1):
            for j in range(i + 2, len(word) + 1):
                substring = word[i:j]
                if len(substring) >= 2 and word.count(substring) > 1:
                    has_repetition = True
                    break
            if has_repetition:
                break
        
        # If word has repetitive patterns and candidate is in dictionary, likely scrambling
        if has_repetition:
            # Additional check: ensure significant character overlap
            overlap = len(set(word.lower()) & set(candidate.lower()))
            total_unique = len(set(word.lower()) | set(candidate.lower()))
            if overlap / total_unique > 0.7:
                return True
        
        return False
    
    def _is_intentional_scrambling(self, word, correct_word):
        """Determine if the scrambling pattern suggests intentional jumbling"""
        
        if len(word) != len(correct_word):
            return False
        
        # Special case: if only the last character differs, it's likely a typo, not scrambling
        if word[:-1] == correct_word[:-1] and word[-1] != correct_word[-1]:
            return False  # This is a simple character substitution, not scrambling
        
        # Special case: if only the first character differs, it's likely a typo
        if word[1:] == correct_word[1:] and word[0] != correct_word[0]:
            return False
        
        # Special case: For anagrams, check if they're meaningful scrambling pairs
        if sorted(word.lower()) == sorted(correct_word.lower()):
            # Check if this is a meaningful scrambling relationship
            if not self._is_meaningful_scrambling_pair(word, correct_word):
                return False
        
        # Check for patterns that suggest intentional scrambling
        # 1. More than 2 positions changed AND not a simple typo pattern
        different_positions = sum(1 for i, (a, b) in enumerate(zip(word, correct_word)) if a != b)
        
        # For short words, be more strict about what counts as scrambling
        if len(word) <= 5:
            # If only 2 characters differ and they're adjacent, it's likely a typo
            if different_positions == 2:
                diff_indices = [i for i, (a, b) in enumerate(zip(word, correct_word)) if a != b]
                if len(diff_indices) == 2 and abs(diff_indices[0] - diff_indices[1]) == 1:
                    return False  # Adjacent swap = typo
                # Single character substitution that creates anagram = still likely typo  
                if self._is_single_character_error_anagram(word, correct_word):
                    return False
            
            # For 5-letter words, need at least 3 different positions for scrambling
            if different_positions < 3:
                return False
        
        # 2. More complex rearrangement patterns (not simple adjacent swaps)
        if different_positions >= 3 and not self._is_simple_typo_sequence(word, correct_word):
            return True
        
        # 3. For longer words, need more significant changes
        if len(word) > 5 and different_positions > len(word) // 2:
            return True
        
        return False
    
    def _is_meaningful_scrambling_pair(self, word, candidate):
        """Check if word and candidate form a meaningful scrambling pair"""
        
        # Look for patterns that suggest intentional scrambling rather than random anagrams
        
        # 1. Check for repetitive patterns in the input word (like "ababe")
        word_has_repetition = self._has_repetitive_pattern(word)
        candidate_has_repetition = self._has_repetitive_pattern(candidate)
        
        # If input has repetition but target doesn't, it's likely scrambling
        if word_has_repetition and not candidate_has_repetition:
            return True
        
        # 2. Check if the target word is significantly more "natural" looking
        # This is heuristic but helps distinguish meaningful words from random combinations
        if self._looks_more_natural(candidate, word):
            return True
        
        # 3. For common patterns like vowel-consonant alternation
        if self._has_natural_vowel_pattern(candidate) and not self._has_natural_vowel_pattern(word):
            return True
        
        return False
    
    def _has_repetitive_pattern(self, word):
        """Check if word has repetitive substrings"""
        for i in range(len(word) - 1):
            for j in range(i + 2, len(word) + 1):
                substring = word[i:j]
                if len(substring) >= 2 and word.count(substring) > 1:
                    return True
        return False
    
    def _looks_more_natural(self, word1, word2):
        """Heuristic to check if word1 looks more natural than word2"""
        
        # Check for better vowel-consonant distribution
        vowels = 'aeiou'
        
        def vowel_consonant_score(w):
            score = 0
            for i in range(len(w) - 1):
                curr_is_vowel = w[i].lower() in vowels
                next_is_vowel = w[i + 1].lower() in vowels
                # Reward alternating vowel-consonant patterns
                if curr_is_vowel != next_is_vowel:
                    score += 1
            return score
        
        return vowel_consonant_score(word1) > vowel_consonant_score(word2)
    
    def _has_natural_vowel_pattern(self, word):
        """Check if word has a natural vowel-consonant pattern"""
        vowels = 'aeiou'
        vowel_positions = [i for i, c in enumerate(word.lower()) if c in vowels]
        
        # Check for reasonable vowel distribution
        if len(vowel_positions) == 0:
            return False
        
        # Words should typically have vowels distributed throughout
        if len(vowel_positions) >= 2:
            # Check if vowels are reasonably spaced
            max_gap = max(vowel_positions[i+1] - vowel_positions[i] for i in range(len(vowel_positions)-1))
            return max_gap <= 3  # No huge gaps between vowels
        
        return True
    
    def _is_single_character_error_anagram(self, word, correct_word):
        """Check if this is a single character substitution that happens to create an anagram"""
        if len(word) != len(correct_word):
            return False
        
        differences = sum(1 for a, b in zip(word, correct_word) if a != b)
        # If exactly 2 differences and it's an anagram, it might be a substitution
        # where the substituted character appears elsewhere in the word
        return differences == 2 and sorted(word) == sorted(correct_word)
    
    def _is_simple_typo_sequence(self, word, correct_word):
        """Check if the changes follow simple typo patterns"""
        
        # Check for single character substitution
        if self._is_single_character_error(word, correct_word):
            return True
        
        # Check for simple adjacent swap
        if self._is_simple_adjacent_swap(word, correct_word):
            return True
        
        # Check for keyboard proximity errors (common typos)
        if self._is_keyboard_proximity_error(word, correct_word):
            return True
        
        return False
    
    def _is_keyboard_proximity_error(self, word, correct_word):
        """Check if the error involves keys that are close on a QWERTY keyboard"""
        
        if len(word) != len(correct_word):
            return False
        
        # Define keyboard proximity (simplified)
        keyboard_neighbors = {
            'a': 'sqw', 'b': 'vghn', 'c': 'xdfv', 'd': 'erfcxs', 'e': 'wrsdf',
            'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'i': 'ujklo', 'j': 'uikmnh',
            'k': 'ijolm', 'l': 'okp', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
            'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'awedx', 't': 'ryfg',
            'u': 'yihj', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tugh',
            'z': 'asx'
        }
        
        differences = sum(1 for a, b in zip(word, correct_word) if a != b)
        if differences == 1:
            # Find the different character
            for i, (a, b) in enumerate(zip(word, correct_word)):
                if a != b:
                    # Check if they're keyboard neighbors
                    if b.lower() in keyboard_neighbors.get(a.lower(), ''):
                        return True
        
        return False
    
    def _is_simple_adjacent_swap(self, word, correct_word):
        """Check if the difference is just adjacent character swaps (common typo)"""
        
        if len(word) != len(correct_word):
            return False
        
        # Find all positions where characters differ
        diff_positions = [i for i, (a, b) in enumerate(zip(word, correct_word)) if a != b]
        
        # For adjacent swaps, we should have exactly 2 different positions that are adjacent
        if len(diff_positions) == 2 and abs(diff_positions[0] - diff_positions[1]) == 1:
            i, j = diff_positions
            # Check if swapping these positions gives the correct word
            word_list = list(word)
            word_list[i], word_list[j] = word_list[j], word_list[i]
            return ''.join(word_list) == correct_word
        
        return False
    
    def _is_likely_typo_enhanced(self, word):
        """Enhanced detection for genuine typos"""
        
        # Get best match
        best_match = process.extractOne(
            word, self.words, scorer=fuzz.ratio, score_cutoff=50
        )
        
        if not best_match:
            return False
        
        match_word, score, _ = best_match
        
        # Rule 1: Very high similarity (likely a typo)
        if score >= 85:
            return True
        
        # Rule 2: Check for specific typo patterns
        if self._has_enhanced_typo_patterns(word, match_word):
            return True
        
        # Rule 3: Edit distance analysis
        if self._is_reasonable_edit_distance(word, match_word, score):
            return True
        
        return False
    
    def _has_enhanced_typo_patterns(self, word, correct_word):
        """Enhanced common typo pattern detection"""
        
        # 1. Single character substitution (like "babai" -> "babae")
        if self._is_single_character_error(word, correct_word):
            return True
        
        # 2. Simple adjacent character swap (like "babye" -> "babae")
        if self._is_simple_adjacent_swap(word, correct_word):
            return True
        
        # 3. Single character insertion/deletion
        if abs(len(word) - len(correct_word)) == 1:
            longer = word if len(word) > len(correct_word) else correct_word
            shorter = correct_word if len(word) > len(correct_word) else word
            
            # Check if one is substring of the other with one insertion/deletion
            for i in range(len(longer)):
                if longer[:i] + longer[i+1:] == shorter:
                    return True
        
        # 4. Double character (like "babae" -> "babaae" or "babae" -> "babe")
        if self._is_double_character_error(word, correct_word):
            return True
        
        return False
    
    def _is_double_character_error(self, word, correct_word):
        """Detect doubled or missing doubled characters"""
        
        # Check for accidental doubling (like "babaae" from "babae")
        if len(word) == len(correct_word) + 1:
            for i in range(len(word) - 1):
                if word[i] == word[i + 1]:  # Found a double
                    test_word = word[:i] + word[i+1:]  # Remove one occurrence
                    if test_word == correct_word:
                        return True
        
        # Check for missing doubling (like "babe" from "babae")
        if len(word) == len(correct_word) - 1:
            for i in range(len(correct_word) - 1):
                if correct_word[i] == correct_word[i + 1]:  # Found a double in correct
                    test_word = correct_word[:i] + correct_word[i+1:]  # Remove one occurrence
                    if test_word == word:
                        return True
        
        return False
    
    def _is_reasonable_edit_distance(self, word, correct_word, similarity_score):
        """Check if the edit distance is reasonable for a typo"""
        
        # Calculate rough edit distance from similarity score
        max_len = max(len(word), len(correct_word))
        estimated_edits = max_len * (100 - similarity_score) / 100
        
        # For typos, we expect small edit distances
        if len(word) <= 4 and estimated_edits <= 1.5:
            return True
        elif len(word) <= 8 and estimated_edits <= 2.5:
            return True
        elif len(word) > 8 and estimated_edits <= 3.0:
            return True
        
        return False

    def _get_typo_suggestions(self, word, limit, score_cutoff):
        """Get suggestions for genuine typos with enhanced scoring"""
        
        # Use multiple scoring methods
        ratio_suggestions = process.extract(
            word, self.words, scorer=fuzz.ratio, limit=limit*3, score_cutoff=score_cutoff-10
        )
        
        token_suggestions = process.extract(
            word, self.words, scorer=fuzz.token_ratio, limit=limit*2, score_cutoff=score_cutoff-20
        )
        
        # Combine and deduplicate with enhanced scoring
        all_suggestions = {}
        
        for suggestion, score, _ in ratio_suggestions:
            # Boost score for typo patterns
            enhanced_score = self._enhance_typo_score(word, suggestion, score)
            all_suggestions[suggestion] = max(all_suggestions.get(suggestion, 0), enhanced_score)
        
        for suggestion, score, _ in token_suggestions:
            # Give token ratio slightly less weight but still enhance
            enhanced_score = self._enhance_typo_score(word, suggestion, score * 0.9)
            all_suggestions[suggestion] = max(all_suggestions.get(suggestion, 0), enhanced_score)
        
        # Sort by enhanced score and frequency
        suggestions = sorted(
            all_suggestions.items(),
            key=lambda x: (x[1], self.frequencies.get(x[0], 0)),
            reverse=True
        )
        
        return [s[0] for s in suggestions[:limit]]
    
    def _enhance_typo_score(self, word, suggestion, base_score):
        """Enhance scoring for suggestions that match common typo patterns"""
        
        enhanced_score = base_score
        
        # MAJOR boost for character substitution at end of word (very common)
        # This specifically helps "babai" -> "babae"
        if (len(word) == len(suggestion) and 
            word[:-1] == suggestion[:-1] and 
            word[-1] != suggestion[-1]):
            enhanced_score += 30  # Increased from 25
        
        # MAJOR boost for character substitution at beginning of word
        if (len(word) == len(suggestion) and 
            word[1:] == suggestion[1:] and 
            word[0] != suggestion[0]):
            enhanced_score += 25  # Increased from 20
        
        # Major boost for single character errors (most common typos)
        if self._is_single_character_error(word, suggestion):
            enhanced_score += 20
        
        # Boost for keyboard proximity errors
        if self._is_keyboard_proximity_error(word, suggestion):
            enhanced_score += 18
        
        # Boost for simple adjacent swaps
        if self._is_simple_adjacent_swap(word, suggestion):
            enhanced_score += 15
        
        # Boost for single insertion/deletion
        if abs(len(word) - len(suggestion)) == 1:
            if self._has_enhanced_typo_patterns(word, suggestion):
                enhanced_score += 12
        
        # Boost for double character errors
        if self._is_double_character_error(word, suggestion):
            enhanced_score += 10
        
        # Boost for same starting characters (common in typing errors)
        if len(word) >= 2 and len(suggestion) >= 2:
            if word[:2].lower() == suggestion[:2].lower():
                enhanced_score += 8
        
        # Boost for same ending characters (except the last char substitution which is already boosted)
        if len(word) >= 3 and len(suggestion) >= 3:
            if word[-3:-1].lower() == suggestion[-3:-1].lower():
                enhanced_score += 6
        
        # Extra boost for dictionary frequency
        word_freq = self.frequencies.get(suggestion, 0)
        if word_freq > 5:  # Lowered threshold since max frequencies are low
            enhanced_score += 8
        elif word_freq > 2:
            enhanced_score += 5
        elif word_freq > 0:
            enhanced_score += 2
        
        # Special boost for semantically important/common words that might have low frequency in this dictionary
        common_important_words = {
            'babae', 'lalaki', 'tao', 'anak', 'pamilya', 'bahay', 'gulo', 'tubig', 
            'araw', 'gabi', 'buwan', 'taon', 'oras', 'mabuti', 'masama', 'malaki', 
            'maliit', 'kumain', 'uminom', 'matulog', 'maganda', 'pangit'
        }
        
        if suggestion.lower() in common_important_words:
            enhanced_score += 15  # Extra boost for important words
        
        return enhanced_score  # Remove the cap to allow important words to score higher
    
    def _is_anagram(self, word1, word2):
        """Check if two words are anagrams (same letters, different order)"""
        return sorted(word1.lower()) == sorted(word2.lower())
    
    def _is_likely_foreign(self, word):
        """Detect if word is likely a foreign word or name"""
        
        # Handle empty or very short words
        if len(word) == 0:
            return True
        if len(word) == 1:
            return False  # Single letters might be valid Tagalog
        
        # Rule 1: Capitalized words might be names
        if word[0].isupper() and len(word) > 2:
            return True
        
        # Rule 2: Contains character patterns uncommon in Tagalog
        foreign_patterns = [
            r'[qxz]',  # Letters rarely used in Tagalog
            r'[ck]h',  # 'ch' and 'ck' combinations
            r'[aeiou]{3,}',  # Long vowel sequences
            r'[bcdfghjklmnpqrstvwxyz]{4,}',  # Long consonant clusters
        ]
        
        for pattern in foreign_patterns:
            if re.search(pattern, word.lower()):
                return True
        
        # Rule 3: No close Tagalog matches at all
        best_match = process.extractOne(
            word, self.words, scorer=fuzz.ratio, score_cutoff=30
        )
        
        if not best_match or best_match[1] < 30:
            return True
        
        return False
    
    def _is_single_character_error(self, word, correct_word):
        """Check if words differ by exactly one character"""
        if len(word) != len(correct_word):
            return False
        
        differences = sum(1 for a, b in zip(word, correct_word) if a != b)
        return differences == 1

    def get_definition(self, word):
        """Get definition from online dictionary if available"""
        if self.online_dict:
            return self.online_dict.get_definition(word)
        return None
    
    def get_stats(self):
        """Get statistics about the dictionaries"""
        return {
            'local_words': len(self.local_words),
            'online_words': len(self.online_words),
            'total_words': len(self.words),
            'online_enabled': self.online_dict is not None
        }
    
    def _has_strong_scrambling_evidence(self, word, target):
        """Check for strong evidence of scrambling for high-similarity anagrams"""
        
        # Must be same length
        if len(word) != len(target):
            return False
        
        # Check different positions
        different_positions = sum(1 for a, b in zip(word, target) if a != b)
        
        # For high-similarity matches, require substantial rearrangement (4+ positions)
        if different_positions < 4:
            return False
        
        # Target should be very common or very important
        target_freq = self.frequencies.get(target, 0)
        important_words = self._get_common_words()
        
        # Only consider it strong scrambling if:
        # 1. Target is in our important words list AND has high frequency, OR
        # 2. Target has very high frequency (>10)
        if ((target in important_words and target_freq > 5) or 
            target_freq > 10):
            return True
        
        return False
