#!/usr/bin/env python
"""
Quick verification that Phase 8 is active and configured correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from game_seg_trivia.content_retrieval import USE_PDF_RATIO
from baybayin_codex_pdf.models import PDFCodexEntry
from baybayin_codex.models import CodexArticle, CodexGlossary

print("=" * 60)
print("PHASE 8 STATUS CHECK")
print("=" * 60)

# Check configuration
print(f"\n✓ Configuration:")
print(f"  USE_PDF_RATIO = {USE_PDF_RATIO}")

if USE_PDF_RATIO == 1.0:
    print(f"  ✅ PHASE 8 ACTIVE - 100% PDF mode enabled")
elif USE_PDF_RATIO >= 0.8:
    print(f"  ⚠️  High PDF ratio ({int(USE_PDF_RATIO*100)}%) - mostly PDF")
elif USE_PDF_RATIO >= 0.5:
    print(f"  ⚠️  Balanced mode ({int(USE_PDF_RATIO*100)}% PDF)")
else:
    print(f"  ❌ Shadow mode ({int(USE_PDF_RATIO*100)}% PDF) - NOT Phase 8")

# Check data availability
pdf_count = PDFCodexEntry.objects.count()
web_article_count = CodexArticle.objects.count()
web_glossary_count = CodexGlossary.objects.count()

print(f"\n✓ Data availability:")
print(f"  PDF entries: {pdf_count}")
print(f"  Web articles: {web_article_count}")
print(f"  Web glossaries: {web_glossary_count}")

# Calculate what will be retrieved
top_k = 3
pdf_facts = int(top_k * USE_PDF_RATIO)
web_facts = top_k - pdf_facts

print(f"\n✓ When retrieving {top_k} facts:")
print(f"  PDF facts: {pdf_facts}")
print(f"  Web facts: {web_facts}")

# Summary
print(f"\n{'='*60}")
if USE_PDF_RATIO == 1.0 and pdf_count > 0:
    print("✅ READY: Trivia will use 100% PDF content")
    print("\nWeb articles remain available for UI browsing.")
elif pdf_count == 0:
    print("❌ ERROR: No PDF entries found!")
    print("\nRun: python manage.py ingest_pdf path/to/your.pdf")
else:
    print(f"ℹ️  INFO: Using {int(USE_PDF_RATIO*100)}% PDF, {int((1-USE_PDF_RATIO)*100)}% Web")
    print("\nTo activate Phase 8, set USE_PDF_RATIO=1.0")

print("=" * 60)
