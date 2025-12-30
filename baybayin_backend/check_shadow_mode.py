#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from baybayin_codex_pdf.models import PDFCodexEntry
from baybayin_codex.models import CodexArticle, CodexGlossary

print("=" * 60)
print("SHADOW MODE CONFIGURATION")
print("=" * 60)

# Get the PDF ratio from environment or default
USE_PDF_RATIO = float(os.getenv("USE_PDF_RATIO", "0.2"))

print(f"\nCurrent Configuration:")
print(f"  PDF Ratio: {USE_PDF_RATIO} ({int(USE_PDF_RATIO*100)}%)")
print(f"  Web Ratio: {1-USE_PDF_RATIO} ({int((1-USE_PDF_RATIO)*100)}%)")
print(f"\n  When retrieving 3 facts:")
print(f"    - PDF facts: {int(3 * USE_PDF_RATIO)}")
print(f"    - Web facts: {3 - int(3 * USE_PDF_RATIO)}")

print("\n" + "=" * 60)
print("DATA AVAILABILITY")
print("=" * 60)

pdf_count = PDFCodexEntry.objects.count()
article_count = CodexArticle.objects.count()
glossary_count = CodexGlossary.objects.count()

print(f"\nPDF Entries: {pdf_count}")
print(f"Web Articles: {article_count}")
print(f"Web Glossaries: {glossary_count}")
print(f"Total Web Facts: {article_count + glossary_count}")

print("\n" + "=" * 60)
print("SAMPLE PDF FACTS")
print("=" * 60)

print("\nShowing 3 random PDF entries:\n")
for i, entry in enumerate(PDFCodexEntry.objects.order_by('?')[:3], 1):
    print(f"{i}. Page {entry.page_number}, Chunk {entry.chunk_index}")
    print(f"   Text: {entry.text[:200]}...")
    print()

print("=" * 60)
print("ENVIRONMENT VARIABLE OPTIONS")
print("=" * 60)
print("\nTo change PDF ratio, set environment variable:")
print("  Windows: set USE_PDF_RATIO=0.5")
print("  Linux/Mac: export USE_PDF_RATIO=0.5")
print("\nRecommended migration path:")
print("  Phase 1: USE_PDF_RATIO=0.2 (20% PDF - testing)")
print("  Phase 2: USE_PDF_RATIO=0.5 (50% PDF - balanced)")
print("  Phase 3: USE_PDF_RATIO=0.8 (80% PDF - mostly PDF)")
print("  Phase 4: USE_PDF_RATIO=1.0 (100% PDF - full migration)")
print()
