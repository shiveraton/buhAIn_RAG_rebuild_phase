#!/usr/bin/env python3
"""
Test script for Tagalog Spelling Checker phrase-level suggestions
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tagalog_spelling_checker.checker import TagalogSpellingChecker

def test_phrase_suggestions():
    # Initialize checker
    dict_path = "data/dictionary/tagalog_words.txt"
    checker = TagalogSpellingChecker(dict_path, use_online=False)
    
    # Test cases
    test_cases = [
        "magasnda Sko",  # Should suggest: "maganda ako", "maghanda ako", "maganda sako"
        "kumian ka na",  # Should suggest variations of "kumain ka na"
        "ako ay maalaga",  # Should suggest variations with "mabait" or other corrections
    ]
    
    print("Testing Tagalog Spelling Checker Phrase-Level Suggestions")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{text}'")
        print("-" * 40)
        
        result = checker.check_text(text, limit=5, score_cutoff=60)
        
        print(f"Input: {result['input']}")
        print(f"Normalized: {result['normalized']}")
        print(f"Is Correct: {result['is_correct']}")
        
        print("\nWord-level results:")
        for j, word_result in enumerate(result['results']):
            print(f"  {j+1}. '{word_result['word']}' -> Correct: {word_result['correct']}")
            if word_result['suggestions']:
                print(f"      Suggestions: {word_result['suggestions']}")
        
        print(f"\nPhrase-level suggestions ({len(result['suggestions'])}):")
        for j, suggestion in enumerate(result['suggestions'], 1):
            print(f"  {j}. '{suggestion}'")
        
        print()

if __name__ == "__main__":
    test_phrase_suggestions()
