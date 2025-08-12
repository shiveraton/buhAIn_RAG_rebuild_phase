#!/usr/bin/env python3
"""
Enhanced Tagalog Spelling Checker Test Script
Tests the improved phrase suggestion functionality with contextual Tagalog patterns.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tagalog_spelling_checker.checker import TagalogSpellingChecker

def test_enhanced_phrase_suggestions():
    """Test the enhanced phrase suggestion functionality"""
    
    # Initialize checker
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dictionary", "tagalog_dictionary.txt")
    checker = TagalogSpellingChecker(dict_path)
    
    print("=" * 60)
    print("ENHANCED TAGALOG SPELLING CHECKER - PHRASE SUGGESTIONS TEST")
    print("=" * 60)
    print()
    
    # Test cases with different types of errors and contexts
    test_cases = [
        {
            "input": "maganda akoo",
            "description": "Simple phrase with typo in pronoun"
        },
        {
            "input": "ang mga babea ay maganda",
            "description": "Article + plural + noun with typo + predicate"
        },
        {
            "input": "si maria ay mabait na bata",
            "description": "Person name + predicate with adjective"
        },
        {
            "input": "kumain ako ng pagkian",
            "description": "Verb + pronoun + marker + noun with typo"
        },
        {
            "input": "sa bahay ng mga kaibigam",
            "description": "Prepositional phrase with typo in last word"
        },
        {
            "input": "mag aral ako para sa paaralaan",
            "description": "Verb phrase + purpose clause (space issue in verb)"
        },
        {
            "input": "hindi ko alam kung ano yan",
            "description": "Negative + pronoun + verb + interrogative"
        },
        {
            "input": "mga babae ay mahusay sa pagtrabaho",
            "description": "Plural noun + predicate + skill description"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {case['description']}")
        print(f"Input: '{case['input']}'")
        print("-" * 40)
        
        result = checker.check_text(case['input'])
        
        print(f"Is Correct: {result['is_correct']}")
        print(f"Normalized: '{result['normalized']}'")
        print()
        
        # Show per-word analysis
        print("Per-word Analysis:")
        for word_result in result['results']:
            status = "✓" if word_result['correct'] else "✗"
            print(f"  {status} '{word_result['word']}' -> {word_result['suggestions'][:3] if word_result['suggestions'] else 'No suggestions'}")
        print()
        
        # Show enhanced phrase suggestions
        if result['suggestions']:
            print("Enhanced Phrase Suggestions:")
            for j, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {j}. '{suggestion}'")
        else:
            print("No phrase suggestions generated")
        
        print()
        print("=" * 60)
        print()

def test_contextual_scoring():
    """Test specific contextual scoring features"""
    
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dictionary", "tagalog_dictionary.txt")
    checker = TagalogSpellingChecker(dict_path)
    
    print("CONTEXTUAL SCORING TESTS")
    print("=" * 40)
    print()
    
    # Test word pair scoring
    test_pairs = [
        ("ang", "mga"),
        ("mga", "babae"),
        ("sa", "bahay"),
        ("ay", "maganda"),
        ("para", "sa"),
        ("hindi", "ko")
    ]
    
    print("Word Pair Scoring:")
    for prev_word, current_word in test_pairs:
        score = checker._score_word_pair(prev_word, current_word)
        print(f"  '{prev_word}' + '{current_word}' -> {score} points")
    print()
    
    # Test phrase validation
    test_phrases = [
        "ang mga babae ay maganda",
        "ang ang babae",  # Invalid: double article
        "mga mga tao",    # Invalid: double mga
        "si maria ay mabait",
        "kumain ako ng pagkain",
        "sa kay maria"    # Invalid: double preposition
    ]
    
    print("Phrase Validation:")
    for phrase in test_phrases:
        is_valid = checker._validate_phrase_context(phrase, phrase)
        status = "✓" if is_valid else "✗"
        print(f"  {status} '{phrase}'")
    print()

if __name__ == "__main__":
    test_enhanced_phrase_suggestions()
    test_contextual_scoring()
