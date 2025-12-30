"""
Management command to re-process existing PDF entries with enhanced OCR sanitization
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from baybayin_codex_pdf.models import PDFCodexEntry
from baybayin_codex_pdf.text_sanitizer import sanitize_ocr_text
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Re-process existing PDF entries with enhanced OCR text sanitization'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of entries to process in each batch (default: 50)'
        )
        parser.add_argument(
            '--min-confidence',
            type=float,
            default=0.3,
            help='Minimum confidence threshold to reprocess entries (default: 0.3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reprocess all entries regardless of existing confidence scores'
        )
        parser.add_argument(
            '--entry-ids',
            nargs='+',
            type=int,
            help='Process specific entry IDs only'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        min_confidence = options['min_confidence']
        dry_run = options['dry_run']
        force = options['force']
        entry_ids = options.get('entry_ids')
        
        self.stdout.write(
            self.style.SUCCESS('🧹 OCR Text Sanitization Batch Processor')
        )
        self.stdout.write('=' * 60)
        
        # Build query
        queryset = PDFCodexEntry.objects.all()
        
        if entry_ids:
            queryset = queryset.filter(id__in=entry_ids)
            self.stdout.write(f"Processing specific entries: {entry_ids}")
        elif not force:
            # Only process entries that haven't been sanitized or have low confidence
            queryset = queryset.filter(
                models.Q(ocr_confidence_score__isnull=True) |
                models.Q(ocr_confidence_score__lt=min_confidence)
            )
            self.stdout.write(f"Processing entries with confidence < {min_confidence}")
        else:
            self.stdout.write("Force mode: Processing ALL entries")
        
        total_entries = queryset.count()
        
        if total_entries == 0:
            self.stdout.write(
                self.style.WARNING('No entries found matching criteria.')
            )
            return
        
        self.stdout.write(f"Found {total_entries} entries to process")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            
            # Show sample entries that would be processed
            sample_entries = queryset[:5]
            for entry in sample_entries:
                self.stdout.write(
                    f"  • Entry {entry.id}: {entry.text[:50]}..."
                )
            
            if total_entries > 5:
                self.stdout.write(f"  ... and {total_entries - 5} more entries")
            
            return
        
        # Process in batches
        processed = 0
        improved = 0
        errors = 0
        
        self.stdout.write(f"\nStarting batch processing...")
        
        for batch_start in range(0, total_entries, batch_size):
            batch_entries = queryset[batch_start:batch_start + batch_size]
            
            self.stdout.write(
                f"\nProcessing batch {batch_start//batch_size + 1} "
                f"({batch_start + 1}-{min(batch_start + batch_size, total_entries)}/{total_entries})"
            )
            
            with transaction.atomic():
                for entry in batch_entries:
                    try:
                        # Store original values
                        original_text = entry.text
                        original_cleaned = entry.cleaned_text
                        
                        # Apply sanitization to the raw text
                        cleaned_text, stats = sanitize_ocr_text(original_text)
                        
                        # Check if there's improvement
                        confidence = stats['confidence_score']
                        is_improvement = (
                            entry.ocr_confidence_score is None or
                            confidence > entry.ocr_confidence_score or
                            len(cleaned_text.strip()) > len(original_cleaned.strip())
                        )
                        
                        if is_improvement:
                            # Update entry
                            entry.cleaned_text = cleaned_text
                            entry.ocr_sanitization_stats = stats
                            entry.ocr_confidence_score = confidence
                            entry.ocr_config_used = stats.get('ocr_config_used', 'sanitizer')
                            entry.save()
                            
                            improved += 1
                            
                            self.stdout.write(
                                f"  ✅ Entry {entry.id}: "
                                f"Confidence {confidence:.2f}, "
                                f"{stats['total_fixes']} fixes applied"
                            )
                        else:
                            self.stdout.write(
                                f"  ⏭️  Entry {entry.id}: No improvement (confidence {confidence:.2f})"
                            )
                        
                        processed += 1
                        
                    except Exception as e:
                        errors += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"  ❌ Entry {entry.id} failed: {str(e)}"
                            )
                        )
                        logger.error(f"Failed to process entry {entry.id}: {str(e)}")
            
            # Progress update
            progress = (processed / total_entries) * 100
            self.stdout.write(f"Progress: {progress:.1f}% ({processed}/{total_entries})")
        
        # Final summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS('✅ Batch processing complete!')
        )
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"  • Total processed: {processed}")
        self.stdout.write(f"  • Improved: {improved}")
        self.stdout.write(f"  • Errors: {errors}")
        self.stdout.write(f"  • Success rate: {(processed-errors)/max(1,processed)*100:.1f}%")
        
        if improved > 0:
            self.stdout.write(f"\n🎉 Successfully improved {improved} entries!")
            self.stdout.write("The enhanced text sanitization should improve RAG quality.")
        
        # Show some statistics about improvements
        if improved > 0:
            self.stdout.write("\n📈 Improvement Statistics:")
            
            # Get some sample improved entries
            improved_entries = PDFCodexEntry.objects.filter(
                ocr_confidence_score__isnull=False,
                ocr_sanitization_stats__isnull=False
            ).order_by('-ocr_confidence_score')[:5]
            
            for entry in improved_entries:
                stats = entry.ocr_sanitization_stats
                self.stdout.write(
                    f"  • Entry {entry.id}: "
                    f"Confidence {entry.ocr_confidence_score:.2f}, "
                    f"Compression {stats.get('compression_ratio', 0):.2f}, "
                    f"{stats.get('total_fixes', 0)} total fixes"
                )
        
        # Recommendations
        self.stdout.write("\n💡 Next Steps:")
        self.stdout.write("  • Review entries with low confidence scores")
        self.stdout.write("  • Consider re-running OCR on very low confidence entries")
        self.stdout.write("  • Monitor RAG question quality improvements")
        self.stdout.write("  • Update embedding generation to use cleaned_text field")
