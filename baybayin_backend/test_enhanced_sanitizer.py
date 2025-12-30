"""
Test the enhanced OCR sanitizer with real problematic examples
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from baybayin_codex_pdf.text_sanitizer import OCRTextSanitizer

def test_examples():
    sanitizer = OCRTextSanitizer()
    
    # Example 1 from user
    example1 = """ambansa ang savsatiw, kailangang umakma ng mga titik nito sa mga titik na likas sa ibang pamayanang kultural na hindi naman tikeas sa 'Tagalog tulad ng Uf], (jl, [vl,at Iv. ie"""
    
    # Example 2 from user
    example2 = """una | Kasaysayan do mate yo pila fo 2 bb > lb om Pagan basin i iE Ror arg aan ga cabeza de baanga ma fo sa 'aye Saisag clue, mapupreng mapas slag pegs peas, mag st {tng at (6 Plc yal, slap)."""
    
    print("=" * 80)
    print("TESTING ENHANCED OCR SANITIZER")
    print("=" * 80)
    
    # Test Example 1
    print("\n" + "=" * 80)
    print("EXAMPLE 1 - Original:")
    print("=" * 80)
    print(example1)
    
    cleaned1, stats1 = sanitizer.clean_ocr_text(example1)
    
    print("\n" + "-" * 80)
    print("EXAMPLE 1 - Cleaned:")
    print("-" * 80)
    print(cleaned1)
    
    print("\n" + "-" * 80)
    print("EXAMPLE 1 - Statistics:")
    print("-" * 80)
    print(f"Original length: {stats1.original_length}")
    print(f"Cleaned length: {stats1.cleaned_length}")
    print(f"Unicode errors fixed: {stats1.unicode_errors_fixed}")
    print(f"Broken words merged: {stats1.broken_words_merged}")
    print(f"Hyphenation fixed: {stats1.hyphenation_fixed}")
    print(f"Special chars removed: {stats1.special_chars_removed}")
    print(f"Confidence score: {stats1.confidence_score:.2f}")
    
    # Test Example 2
    print("\n" + "=" * 80)
    print("EXAMPLE 2 - Original:")
    print("=" * 80)
    print(example2)
    
    cleaned2, stats2 = sanitizer.clean_ocr_text(example2)
    
    print("\n" + "-" * 80)
    print("EXAMPLE 2 - Cleaned:")
    print("-" * 80)
    print(cleaned2)
    
    print("\n" + "-" * 80)
    print("EXAMPLE 2 - Statistics:")
    print("-" * 80)
    print(f"Original length: {stats2.original_length}")
    print(f"Cleaned length: {stats2.cleaned_length}")
    print(f"Unicode errors fixed: {stats2.unicode_errors_fixed}")
    print(f"Broken words merged: {stats2.broken_words_merged}")
    print(f"Hyphenation fixed: {stats2.hyphenation_fixed}")
    print(f"Special chars removed: {stats2.special_chars_removed}")
    print(f"Confidence score: {stats2.confidence_score:.2f}")
    
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"\nExample 1 Reduction: {stats1.original_length} -> {stats1.cleaned_length} chars ({(1-stats1.cleaned_length/stats1.original_length)*100:.1f}% reduction)")
    print(f"Example 2 Reduction: {stats2.original_length} -> {stats2.cleaned_length} chars ({(1-stats2.cleaned_length/stats2.original_length)*100:.1f}% reduction)")
    
    print("\n" + "=" * 80)
    print("✓ Testing complete!")
    print("=" * 80)

if __name__ == "__main__":
    test_examples()
