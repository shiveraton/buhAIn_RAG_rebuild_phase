#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from baybayin_codex_pdf.models import PDFCodexEntry
from django.db.models import Count

# Get chunk distribution
stats = PDFCodexEntry.objects.values('page_number').annotate(chunks=Count('id')).order_by('page_number')[:10]
print("First 10 pages chunk distribution:")
for s in stats:
    print(f"  Page {s['page_number']}: {s['chunks']} chunks")

# Get averages
total = PDFCodexEntry.objects.count()
pages = PDFCodexEntry.objects.values('page_number').distinct().count()
print(f"\nTotal entries: {total}")
print(f"Total pages: {pages}")
print(f"Average chunks per page: {total/pages:.1f}")

# Check if embeddings exist
entries_with_embeddings = PDFCodexEntry.objects.exclude(embedding__isnull=True).count()
print(f"\nEntries with embeddings: {entries_with_embeddings}/{total}")
