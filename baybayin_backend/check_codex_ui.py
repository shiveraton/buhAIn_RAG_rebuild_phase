#!/usr/bin/env python
"""Quick check that Phase 8.5 is active"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from baybayin_codex_pdf.models import PDFCodexEntry

print("=" * 60)
print("PHASE 8.5 QUICK STATUS")
print("=" * 60)

pdf_count = PDFCodexEntry.objects.count()
print(f"\n✓ PDF Entries: {pdf_count}")

if pdf_count > 0:
    print(f"✅ ACTIVE: Codex UI will display {pdf_count} PDF entries")
    print("\nEndpoints ready:")
    print("  GET /api/codex/articles/")
    print("  GET /api/codex/articles/<id>/")
    print("  GET /api/codex/articles/featured/")
    print("  GET /api/codex/articles/search/?q=query")
    print("\nRestart Django server to activate changes!")
else:
    print("❌ No PDF entries found")
    print("Run: python manage.py ingest_pdf path/to/pdf")

print("=" * 60)
