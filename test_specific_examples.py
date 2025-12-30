#!/usr/bin/env python3
"""
Test the OCR sanitizer with the specific examples provided by the user
"""

import sys
import os
import django

# Add the Django project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'baybayin_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from baybayin_codex_pdf.text_sanitizer import OCRTextSanitizer

def test_user_examples():
    """Test the sanitizer with the exact examples provided by the user"""
    
    sanitizer = OCRTextSanitizer()
    
    # User's examples
    examples = [
        "ambansa ang savsatiw, kailangang umakma ng mga titik nito sa mga titik na likas sa ibang pamayanang kultural na hindi naman tikeas sa 'Tagalog tulad ng Uf], (jl, [vl,at Iv. ie",
        "una | Kasaysayan do mate yo pila fo 2 bb > lb om Pagan basin i iE Ror arg aan ga cabeza de baanga ma fo sa 'aye Saisag clue, mapupreng mapas slag pegs peas, mag st {tng at (6 Plc yal, slap)."
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"EXAMPLE {i}")
        print(f"{'='*80}")
        print(f"ORIGINAL:")
        print(f"'{example}'")
        print(f"\nLength: {len(example)} characters")
        
        # Clean the text
        cleaned_text, stats = sanitizer.clean_ocr_text(example)
        
        print(f"\nCLEANED:")
        print(f"'{cleaned_text}'")
        print(f"\nLength: {len(cleaned_text)} characters")
        
        print(f"\nSTATISTICS:")
        print(f"  Unicode errors fixed: {stats.unicode_errors_fixed}")
        print(f"  Broken words merged: {stats.broken_words_merged}")
        print(f"  Hyphenation fixed: {stats.hyphenation_fixed}")
        print(f"  Character fixes: {stats.special_chars_removed}")
        print(f"  Confidence score: {stats.confidence_score:.3f}")
        print(f"  Compression ratio: {(len(example) - len(cleaned_text)) / len(example) * 100:.1f}%")
        
        # Show character-by-character differences
        print(f"\nCHARACTER ANALYSIS:")
        original_chars = set(example)
        cleaned_chars = set(cleaned_text)
        removed_chars = original_chars - cleaned_chars
        if removed_chars:
            print(f"  Removed characters: {sorted(removed_chars)}")
        else:
            print(f"  No characters were removed")
            
        # Highlight potential improvements
        print(f"\nPOTENTIAL ISSUES REMAINING:")
        issues = []
        
        # Check for remaining garbage characters
        import re
        garbage_pattern = re.compile(r'[^\w\s\-\'\"\.,\!\?\;\:\(\)\[\]\/\\\u00C0-\u017F\u1E00-\u1EFF]')
        remaining_garbage = garbage_pattern.findall(cleaned_text)
        if remaining_garbage:
            issues.append(f"Remaining special chars: {set(remaining_garbage)}")
        
        # Check for potential broken words (single letters)
        single_chars = re.findall(r'\b[a-zA-Z]\b', cleaned_text)
        if single_chars:
            issues.append(f"Isolated single letters: {single_chars}")
        
        # Check for very short 'words' that might be garbage
        short_words = re.findall(r'\b\w{1,2}\b', cleaned_text)
        if len(short_words) > 3:
            issues.append(f"Many short words (possible fragments): {short_words[:10]}...")
        
        if issues:
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"  No obvious issues detected")

if __name__ == "__main__":
    test_user_examples()
