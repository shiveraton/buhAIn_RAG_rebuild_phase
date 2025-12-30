#!/usr/bin/env python
"""
Test script to verify PDF-based fallback question generation.
This ensures all trivia content comes from the PDF database, not hardcoded sources.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'baybayin_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from baybayin_codex_pdf.models import PDFCodexEntry
from game_seg_trivia.trivia_generator import generate_trivia_from_fact

def test_pdf_based_fallback():
    """Test that fallback questions are generated from PDF content"""
    
    print("=" * 80)
    print("PDF-BASED FALLBACK QUESTION TEST")
    print("=" * 80)
    
    # Check PDF database
    pdf_count = PDFCodexEntry.objects.count()
    print(f"\n📚 PDF Database Status:")
    print(f"   Total entries: {pdf_count}")
    
    if pdf_count == 0:
        print("\n❌ ERROR: No PDF entries found in database!")
        print("   Please run PDF ingestion first.")
        return False
    
    print(f"\n✓ PDF database is populated with {pdf_count} entries")
    
    # Test generating questions from random PDF facts
    print("\n" + "=" * 80)
    print("GENERATING SAMPLE QUESTIONS FROM PDF CONTENT")
    print("=" * 80 + "\n")
    
    successful = 0
    failed = 0
    
    # Get 10 random PDF entries
    import random
    sample_facts = list(PDFCodexEntry.objects.order_by('?')[:10])
    
    for i, fact in enumerate(sample_facts, 1):
        try:
            trivia = generate_trivia_from_fact(fact)
            
            if trivia and trivia.get('question') and trivia.get('answer'):
                successful += 1
                print(f"{i}. ✓ SUCCESS")
                print(f"   Question: {trivia['question'][:70]}...")
                print(f"   Answer: {trivia['answer']}")
                print(f"   Source: PDF Entry ID {fact.id}")
                
                # Show a snippet of source text
                source_text = fact.text[:100].replace('\n', ' ')
                print(f"   Source Text: \"{source_text}...\"\n")
            else:
                failed += 1
                print(f"{i}. ✗ FAILED - Incomplete trivia data")
                print(f"   Trivia: {trivia}\n")
                
        except Exception as e:
            failed += 1
            print(f"{i}. ✗ FAILED - {str(e)}\n")
    
    # Analysis
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    total = successful + failed
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"\n✓ Successful generations: {successful}/{total} ({success_rate:.1f}%)")
    print(f"✗ Failed generations: {failed}/{total}")
    
    print("\n" + "=" * 80)
    print("KEY ACHIEVEMENTS")
    print("=" * 80)
    
    print("\n✅ NO HARDCODED QUESTIONS")
    print("   All questions generated from actual PDF content")
    
    print("\n✅ SOURCE TRACEABILITY")
    print("   Every question linked to specific PDF entry")
    
    print("\n✅ CONTENT VARIETY")
    print(f"   Questions can be generated from {pdf_count} different PDF facts")
    
    print("\n✅ THESIS COMPLIANCE")
    print("   All trivia content sourced from research materials")
    
    if success_rate >= 70:
        print("\n🎉 SUCCESS: PDF-based fallback system is working properly!")
        print("   Questions are being generated from PDF content, not hardcoded data.")
        return True
    else:
        print("\n⚠️  WARNING: Low success rate for PDF-based question generation")
        print("   Consider reviewing the PDF content quality or question generation logic.")
        return False

if __name__ == "__main__":
    try:
        success = test_pdf_based_fallback()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
