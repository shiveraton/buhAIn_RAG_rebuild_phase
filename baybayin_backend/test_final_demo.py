#!/usr/bin/env python3
"""
Final demonstration of enhanced Tagalog phrase suggestions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tagalog_spelling_checker.checker import TagalogSpellingChecker

def test_complex_phrase_suggestions():
    """Test complex phrase suggestions with multiple word combinations"""
    
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dictionary", "tagalog_dictionary.txt")
    checker = TagalogSpellingChecker(dict_path)
    
    print("=" * 70)
    print("ENHANCED TAGALOG SPELL CHECKER - COMPLEX PHRASE SUGGESTIONS")
    print("=" * 70)
    print()
    
    # More challenging test cases
    test_cases = [
        {
            "input": "ang mga estudyatne ay nag aaral sa librar",
            "description": "Multiple typos in academic context"
        },
        {
            "input": "kumian si juan ng masarap na ulam",
            "description": "Dining context with person name"
        },
        {
            "input": "mga batang babea ay naglalro sa hardin",
            "description": "Children playing - multiple errors"
        },
        {
            "input": "hindi ako maraming sa eskwela ngayon",
            "description": "Wrong word choice and context"
        },
        {
            "input": "ang guro ay nagtutro ng matematka sa klase",
            "description": "Classroom context with subject matter"
        },
        {
            "input": "sa umaga ako ay pumunpunta sa paleng",
            "description": "Time reference and market context"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {case['description']}")
        print(f"Input: '{case['input']}'")
        print("-" * 50)
        
        result = checker.check_text(case['input'], limit=5)  # Get more suggestions
        
        print(f"Overall Correct: {result['is_correct']}")
        print()
        
        # Per-word breakdown
        print("Word Analysis:")
        for word_result in result['results']:
            status = "✓" if word_result['correct'] else "✗"
            suggestions_text = ""
            if word_result['suggestions']:
                suggestions_text = f" -> [{', '.join(word_result['suggestions'][:3])}]"
            print(f"  {status} '{word_result['word']}'{suggestions_text}")
        print()
        
        # Enhanced phrase suggestions
        if result['suggestions']:
            print("🔧 Enhanced Phrase Suggestions:")
            for j, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {j}. '{suggestion}'")
        else:
            print("⚠️  No phrase suggestions available")
        
        print()
        print("=" * 70)
        print()

def demonstrate_features():
    """Demonstrate the key features of the enhanced checker"""
    
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dictionary", "tagalog_dictionary.txt")
    checker = TagalogSpellingChecker(dict_path)
    
    print("KEY FEATURES DEMONSTRATION")
    print("=" * 50)
    print()
    
    # Feature 1: Essential word recognition
    print("1. Essential Word Recognition:")
    essential_test_words = ['ako', 'si', 'ng', 'kung', 'hindi', 'mga', 'sa', 'ay']
    for word in essential_test_words:
        status = "✓" if checker.is_correct(word) else "✗"
        print(f"   {status} '{word}'")
    print()
    
    # Feature 2: Contextual word pair scoring
    print("2. Contextual Word Pair Scoring:")
    word_pairs = [
        ('ang', 'mga'),
        ('mga', 'babae'),
        ('hindi', 'ko'),
        ('sa', 'bahay'),
        ('para', 'sa'),
        ('ay', 'maganda')
    ]
    for prev, curr in word_pairs:
        score = checker._score_word_pair(prev, curr)
        print(f"   '{prev}' + '{curr}' = {score} points")
    print()
    
    # Feature 3: Phrase validation
    print("3. Phrase Validation Examples:")
    test_phrases = [
        ("ang mga babae ay maganda", True),
        ("ang ang babae", False),
        ("si maria ay mabait", True),
        ("sa kay maria", False),
        ("kumain ako ng pagkain", True),
        ("mga mga tao", False)
    ]
    for phrase, expected in test_phrases:
        actual = checker._validate_phrase_context(phrase, phrase)
        status = "✓" if actual == expected else "✗"
        result = "Valid" if actual else "Invalid"
        print(f"   {status} '{phrase}' -> {result}")
    print()
    
    print("✨ Enhanced checker ready for production use!")
    print()

if __name__ == "__main__":
    test_complex_phrase_suggestions()
    demonstrate_features()
