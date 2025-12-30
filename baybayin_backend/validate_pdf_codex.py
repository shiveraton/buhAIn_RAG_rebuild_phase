#!/usr/bin/env python
"""
PHASE 7 - COMPREHENSIVE PDF CODEX VALIDATION
Validates all aspects of the PDF ingestion before switching to 100% PDF mode
"""
import os
import django
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')
django.setup()

from baybayin_codex_pdf.models import PDFCodexEntry
from baybayin_codex.models import CodexArticle, CodexGlossary
import json

print("=" * 80)
print("PHASE 7 - PDF CODEX VALIDATION REPORT")
print("=" * 80)

# ============================================================================
# 1. CHECK ENTRY COUNT
# ============================================================================
print("\n[1] ENTRY COUNT")
print("-" * 80)
pdf_count = PDFCodexEntry.objects.count()
web_article_count = CodexArticle.objects.count()
web_glossary_count = CodexGlossary.objects.count()
web_total = web_article_count + web_glossary_count

print(f"PDF Entries:       {pdf_count}")
print(f"Web Articles:      {web_article_count}")
print(f"Web Glossaries:    {web_glossary_count}")
print(f"Total Web Facts:   {web_total}")
print(f"\nPDF/Web Ratio:     {pdf_count}:{web_total} ({pdf_count/web_total:.1f}x more PDF facts)")

if pdf_count < 100:
    print("⚠️  WARNING: Less than 100 PDF entries. Consider ingesting more content.")
else:
    print("✅ PASS: Sufficient PDF entries for migration")

# ============================================================================
# 2. CHECK EMBEDDING SHAPES
# ============================================================================
print("\n[2] EMBEDDING VALIDATION")
print("-" * 80)

entries_with_embeddings = PDFCodexEntry.objects.exclude(embedding__isnull=True).count()
entries_without_embeddings = PDFCodexEntry.objects.filter(embedding__isnull=True).count()

print(f"Entries with embeddings:    {entries_with_embeddings}/{pdf_count}")
print(f"Entries without embeddings: {entries_without_embeddings}/{pdf_count}")

if entries_without_embeddings > 0:
    print(f"⚠️  WARNING: {entries_without_embeddings} entries missing embeddings!")
else:
    print("✅ PASS: All entries have embeddings")

# Check embedding dimensions
sample_entries = PDFCodexEntry.objects.exclude(embedding__isnull=True)[:10]
embedding_dims = set()
invalid_embeddings = 0

for entry in sample_entries:
    try:
        emb = entry.embedding
        if isinstance(emb, list):
            embedding_dims.add(len(emb))
        else:
            invalid_embeddings += 1
    except:
        invalid_embeddings += 1

if len(embedding_dims) == 1:
    print(f"✅ PASS: All embeddings have consistent dimension: {list(embedding_dims)[0]}")
elif len(embedding_dims) > 1:
    print(f"⚠️  WARNING: Inconsistent embedding dimensions found: {embedding_dims}")
else:
    print("❌ FAIL: Could not determine embedding dimensions")

if invalid_embeddings > 0:
    print(f"⚠️  WARNING: {invalid_embeddings} entries have invalid embedding format")

# ============================================================================
# 3. CHECK FOR JUNK CHARACTERS
# ============================================================================
print("\n[3] TEXT QUALITY ANALYSIS")
print("-" * 80)

def analyze_text_quality(text):
    """Analyze text for common OCR issues"""
    issues = []
    
    # Check length
    if len(text) < 40:
        issues.append("too_short")
    
    # Check for too many special characters
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if len(text) > 0 and special_chars / len(text) > 0.3:
        issues.append("too_many_special_chars")
    
    # Check for alphabetic ratio
    alpha_chars = sum(1 for c in text if c.isalpha())
    if len(text) > 0 and alpha_chars / len(text) < 0.5:
        issues.append("low_alpha_ratio")
    
    # Check for broken encoding (common OCR artifacts)
    if any(artifact in text for artifact in ['�', 'ﬁ', 'ﬂ', '◌']):
        issues.append("encoding_artifacts")
    
    # Check for excessive whitespace
    if '   ' in text or '\n\n\n' in text:
        issues.append("excessive_whitespace")
    
    return issues

# Sample analysis
sample_size = min(100, pdf_count)
samples = PDFCodexEntry.objects.all()[:sample_size]

quality_stats = {
    'total': 0,
    'too_short': 0,
    'too_many_special_chars': 0,
    'low_alpha_ratio': 0,
    'encoding_artifacts': 0,
    'excessive_whitespace': 0,
    'clean': 0
}

problematic_entries = []

for entry in samples:
    quality_stats['total'] += 1
    issues = analyze_text_quality(entry.text)
    
    if not issues:
        quality_stats['clean'] += 1
    else:
        for issue in issues:
            quality_stats[issue] += 1
        if len(issues) >= 2:  # Multiple issues = problematic
            problematic_entries.append({
                'id': entry.id,
                'page': entry.page_number,
                'chunk': entry.chunk_index,
                'issues': issues,
                'text': entry.text[:100]
            })

print(f"Analyzed {quality_stats['total']} sample entries:")
print(f"  Clean entries:              {quality_stats['clean']} ({quality_stats['clean']/quality_stats['total']*100:.1f}%)")
print(f"  Too short (<40 chars):      {quality_stats['too_short']}")
print(f"  Too many special chars:     {quality_stats['too_many_special_chars']}")
print(f"  Low alphabetic ratio:       {quality_stats['low_alpha_ratio']}")
print(f"  Encoding artifacts:         {quality_stats['encoding_artifacts']}")
print(f"  Excessive whitespace:       {quality_stats['excessive_whitespace']}")

if quality_stats['clean'] / quality_stats['total'] > 0.7:
    print("✅ PASS: Majority of entries are clean (>70%)")
elif quality_stats['clean'] / quality_stats['total'] > 0.5:
    print("⚠️  WARNING: Moderate text quality (50-70% clean)")
else:
    print("❌ FAIL: Poor text quality (<50% clean)")

if problematic_entries:
    print(f"\n⚠️  Found {len(problematic_entries)} highly problematic entries:")
    for idx, entry in enumerate(problematic_entries[:5], 1):
        print(f"\n  {idx}. Page {entry['page']}, Chunk {entry['chunk']} (ID: {entry['id']})")
        print(f"     Issues: {', '.join(entry['issues'])}")
        print(f"     Text: {entry['text']}...")

# ============================================================================
# 4. CHECK MISSING PARAGRAPHS / COVERAGE
# ============================================================================
print("\n[4] PAGE COVERAGE ANALYSIS")
print("-" * 80)

# Get page distribution
from django.db.models import Count
page_stats = PDFCodexEntry.objects.values('page_number').annotate(
    chunk_count=Count('id')
).order_by('page_number')

pages_with_entries = set(p['page_number'] for p in page_stats)
if pages_with_entries:
    min_page = min(pages_with_entries)
    max_page = max(pages_with_entries)
    total_pages_in_range = max_page - min_page + 1
    missing_pages = set(range(min_page, max_page + 1)) - pages_with_entries
    
    print(f"Page range: {min_page} to {max_page} ({total_pages_in_range} pages)")
    print(f"Pages with content: {len(pages_with_entries)}")
    print(f"Missing pages: {len(missing_pages)}")
    
    if missing_pages and len(missing_pages) <= 10:
        print(f"Missing page numbers: {sorted(missing_pages)}")
    
    coverage = len(pages_with_entries) / total_pages_in_range * 100
    print(f"Coverage: {coverage:.1f}%")
    
    if coverage > 80:
        print("✅ PASS: Good page coverage (>80%)")
    elif coverage > 50:
        print("⚠️  WARNING: Moderate page coverage (50-80%)")
    else:
        print("❌ FAIL: Poor page coverage (<50%)")
    
    # Check for pages with very few chunks (might indicate OCR failure)
    sparse_pages = [p for p in page_stats if p['chunk_count'] < 2]
    if sparse_pages:
        print(f"\n⚠️  {len(sparse_pages)} pages have <2 chunks (possible OCR failures):")
        for p in sparse_pages[:10]:
            print(f"     Page {p['page_number']}: {p['chunk_count']} chunk(s)")

# ============================================================================
# 5. SAMPLE CONTENT PREVIEW
# ============================================================================
print("\n[5] SAMPLE CONTENT PREVIEW")
print("-" * 80)

print("\nShowing 3 random high-quality entries:\n")
clean_entries = []
for entry in PDFCodexEntry.objects.all().order_by('?')[:20]:
    issues = analyze_text_quality(entry.text)
    if not issues or len(issues) <= 1:
        clean_entries.append(entry)
    if len(clean_entries) >= 3:
        break

for i, entry in enumerate(clean_entries, 1):
    print(f"{i}. Page {entry.page_number}, Chunk {entry.chunk_index}")
    print(f"   Length: {len(entry.text)} chars")
    print(f"   Text: {entry.text[:200]}...")
    print()

# ============================================================================
# 6. FINAL RECOMMENDATION
# ============================================================================
print("\n" + "=" * 80)
print("MIGRATION READINESS ASSESSMENT")
print("=" * 80)

checks_passed = 0
checks_total = 5

# Check 1: Sufficient entries
if pdf_count >= 100:
    checks_passed += 1
    print("✅ Sufficient PDF entries")
else:
    print("❌ Insufficient PDF entries")

# Check 2: All embeddings present
if entries_without_embeddings == 0:
    checks_passed += 1
    print("✅ All entries have embeddings")
else:
    print("❌ Some entries missing embeddings")

# Check 3: Consistent embedding dimensions
if len(embedding_dims) == 1:
    checks_passed += 1
    print("✅ Consistent embedding dimensions")
else:
    print("❌ Inconsistent embedding dimensions")

# Check 4: Good text quality
if quality_stats['clean'] / quality_stats['total'] > 0.7:
    checks_passed += 1
    print("✅ Good text quality (>70% clean)")
else:
    print("❌ Poor text quality")

# Check 5: Good page coverage
if 'coverage' in locals() and coverage > 80:
    checks_passed += 1
    print("✅ Good page coverage (>80%)")
else:
    print("❌ Poor page coverage")

print(f"\n{'='*80}")
print(f"OVERALL SCORE: {checks_passed}/{checks_total} checks passed")
print(f"{'='*80}\n")

if checks_passed == checks_total:
    print("🎉 READY FOR PHASE 8: SWITCH TO 100% PDF")
    print("\nNext steps:")
    print("  1. Set USE_PDF_RATIO=1.0 (or update retrieve_relevant_facts to always use PDF)")
    print("  2. Test trivia generation with PDF-only facts")
    print("  3. Monitor for quality issues")
    print("  4. Proceed to Phase 9 (delete web codex) only after thorough testing")
elif checks_passed >= 3:
    print("⚠️  ALMOST READY - Address warnings before migration")
    print("\nRecommended actions:")
    if entries_without_embeddings > 0:
        print("  - Regenerate embeddings for missing entries")
    if quality_stats['clean'] / quality_stats['total'] <= 0.7:
        print("  - Review and clean problematic entries")
        print("  - Consider re-ingesting with better OCR preprocessing")
    if 'coverage' in locals() and coverage <= 80:
        print("  - Check why some pages are missing")
        print("  - Re-ingest if pages were skipped incorrectly")
else:
    print("❌ NOT READY - Critical issues must be fixed")
    print("\nCritical actions required:")
    if pdf_count < 100:
        print("  - Ingest more PDF content")
    if entries_without_embeddings > 0:
        print("  - Generate embeddings for all entries")
    if len(embedding_dims) != 1:
        print("  - Fix embedding dimension inconsistencies")

print()
