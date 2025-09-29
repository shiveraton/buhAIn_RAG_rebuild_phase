#!/usr/bin/env python3
"""
Test script to verify that misspelled words are included in the official output
when user doesn't select a correction from the Tagalog spelling checker.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from transliteration.services import text_transliteration_pipeline

def test_misspelled_words_in_output():
    """Test that misspelled words are included in the output when no correction is applied."""
    
    print("Testing Tagalog Spelling Checker - Misspelled Words in Output")
    print("=" * 60)
    
    # Test cases with intentional misspellings
    test_cases = [
        {
            'input': 'kumsta ka',  # misspelling of 'kumusta ka'
            'description': 'Common misspelling of greeting'
        },
        {
            'input': 'mahal kta',  # misspelling of 'mahal kita' 
            'description': 'Missing letter in "kita"'
        },
        {
            'input': 'mgandang umaga',  # misspelling of 'magandang umaga'
            'description': 'Missing letter in "magandang"'
        },
        {
            'input': 'salamat po',  # correct phrase for comparison
            'description': 'Correctly spelled phrase'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Input: '{test_case['input']}'")
        
        # Test Latin to Baybayin (where spelling check happens before transliteration)
        result, warnings = text_transliteration_pipeline(
            test_case['input'], 
            'to_baybayin'
        )
        
        print(f"   Normalized text: '{result.get('normalized_text', 'N/A')}'")
        print(f"   Transliterated text: '{result.get('transliterated_text', 'N/A')}'")
        
        # Check if spelling metadata is present
        spelling_metadata = result.get('spelling_metadata')
        if spelling_metadata:
            print(f"   Spelling check performed: {not spelling_metadata.get('is_correct', True)}")
            if not spelling_metadata.get('is_correct', True):
                print(f"   Has suggestions: {bool(spelling_metadata.get('suggestions'))}")
                if spelling_metadata.get('suggestions'):
                    print(f"   Suggestions: {spelling_metadata.get('suggestions')}")
                
                # Check if original misspelled text is preserved in spell_checked_text
                spell_checked_text = result.get('spell_checked_text')
                print(f"   Spell-checked text: '{spell_checked_text}'")
                
                # Verify that misspelled words are included when no correction is applied
                if spell_checked_text == test_case['input']:
                    print("   ✓ PASS: Original misspelled text is preserved")
                else:
                    print("   ✗ FAIL: Original misspelled text was automatically corrected")
            else:
                print("   ✓ Text is correctly spelled")
        else:
            print("   No spelling metadata (spelling checker may not be available)")
        
        print(f"   Warnings: {warnings}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

def test_baybayin_to_latin_with_spelling():
    """Test Baybayin to Latin with spelling check on output."""
    
    print("\n\nTesting Baybayin to Latin with Spelling Check")
    print("=" * 50)
    
    # Test with Baybayin input that might result in misspelled Latin output
    baybayin_input = "ᜃᜓᜋᜐ᜔ᜆ"  # should be "kumsta" (misspelling of "kumusta")
    
    print(f"Input (Baybayin): '{baybayin_input}'")
    
    result, warnings = text_transliteration_pipeline(
        baybayin_input, 
        'to_latin'
    )
    
    print(f"Normalized text: '{result.get('normalized_text', 'N/A')}'")
    print(f"Transliterated text: '{result.get('transliterated_text', 'N/A')}'")
    
    # Check spelling metadata on the Latin output
    spelling_metadata = result.get('spelling_metadata')
    if spelling_metadata:
        print(f"Spelling check performed: {not spelling_metadata.get('is_correct', True)}")
        if not spelling_metadata.get('is_correct', True):
            print(f"Has suggestions: {bool(spelling_metadata.get('suggestions'))}")
            if spelling_metadata.get('suggestions'):
                print(f"Suggestions: {spelling_metadata.get('suggestions')}")
            
            # Check if original misspelled result is preserved
            spell_checked_text = result.get('spell_checked_text')
            print(f"Spell-checked text: '{spell_checked_text}'")
            
            if spell_checked_text == result.get('transliterated_text'):
                print("✓ PASS: Original transliterated text (with misspellings) is preserved")
            else:
                print("✗ FAIL: Original transliterated text was automatically corrected")
        else:
            print("✓ Transliterated text is correctly spelled")
    else:
        print("No spelling metadata available")
    
    print(f"Warnings: {warnings}")

if __name__ == "__main__":
    try:
        test_misspelled_words_in_output()
        test_baybayin_to_latin_with_spelling()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()