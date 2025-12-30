"""
Management command to analyze all PDF content with AI
Run: python manage.py analyze_content
"""

from django.core.management.base import BaseCommand, CommandError
from game_seg_trivia.ai_content_analyzer import AIContentAnalyzer
from baybayin_codex_pdf.models import PDFCodexEntry
from django.utils import timezone
import os

class Command(BaseCommand):
    help = 'AI automatically analyzes all PDF content for difficulty and categorization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reanalyze',
            action='store_true',
            help='Reanalyze ALL entries, even those already analyzed',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of entries to analyze (for testing)',
        )
        parser.add_argument(
            '--entry-id',
            type=int,
            help='Analyze specific entry by ID',
        )

    def handle(self, *args, **options):
        self.stdout.write("🤖 Starting AI Content Analysis...")
        
        # Check if API key is available
        api_key = os.environ.get("CHUTES_API_KEY")
        if not api_key:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  CHUTES_API_KEY not found. Using fallback analysis (less accurate)."
                )
            )
        else:
            self.stdout.write(f"✅ Using AI API for analysis")
        
        analyzer = AIContentAnalyzer()
        
        # Handle specific entry
        if options['entry_id']:
            self.stdout.write(f"Analyzing specific entry ID: {options['entry_id']}")
            success = analyzer.reanalyze_entry(options['entry_id'])
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully reanalyzed entry {options["entry_id"]}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to reanalyze entry {options["entry_id"]}')
                )
            return
        
        # Get entries to analyze
        if options['reanalyze']:
            pdf_entries = PDFCodexEntry.objects.all()
            self.stdout.write("🔄 Reanalyzing ALL entries (including previously analyzed)")
        else:
            pdf_entries = PDFCodexEntry.objects.filter(ai_difficulty_score__isnull=True)
            self.stdout.write("📝 Analyzing only unprocessed entries")
        
        if options['limit']:
            pdf_entries = pdf_entries[:options['limit']]
            self.stdout.write(f"📊 Limited to {options['limit']} entries")
        
        total_entries = pdf_entries.count()
        
        if total_entries == 0:
            self.stdout.write(
                self.style.SUCCESS("✨ All entries are already analyzed! Use --reanalyze to force reanalysis.")
            )
            return
        
        self.stdout.write(f"📚 Found {total_entries} entries to analyze")
        self.stdout.write("=" * 60)
        
        # Track progress
        processed = 0
        successful = 0
        failed = 0
        
        # Process entries
        for entry in pdf_entries:
            try:
                self.stdout.write(f"📄 Analyzing entry {entry.id} (page {entry.page_number})...")
                
                # Get content to analyze
                content = entry.cleaned_text or entry.text
                if not content or len(content.strip()) < 10:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Skipping entry {entry.id}: insufficient content")
                    )
                    failed += 1
                    continue
                
                # Analyze with AI
                analysis = analyzer.analyze_content_difficulty(content)
                
                # Update entry with analysis results
                entry.ai_difficulty_score = analysis['difficulty_score']
                entry.ai_category = analysis['category']
                entry.ai_prerequisites = analysis['prerequisites']
                entry.ai_cognitive_level = analysis['cognitive_level']
                entry.ai_estimated_minutes = analysis['estimated_study_minutes']
                entry.ai_analysis_reasoning = analysis['reasoning']
                entry.ai_analyzed_at = timezone.now()
                entry.save()
                
                successful += 1
                processed += 1
                
                # Show progress
                progress_pct = (processed / total_entries) * 100
                self.stdout.write(
                    f"✅ Entry {entry.id}: "
                    f"difficulty={analysis['difficulty_score']:.2f}, "
                    f"category={analysis['category']} "
                    f"({processed}/{total_entries} - {progress_pct:.1f}%)"
                )
                
                # Progress checkpoint every 10 entries
                if processed % 10 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f"🎯 Checkpoint: {processed}/{total_entries} processed")
                    )
                    
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING(f"\n⏹️  Interrupted by user. Processed {processed} entries.")
                )
                break
                
            except Exception as e:
                failed += 1
                processed += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to analyze entry {entry.id}: {str(e)}")
                )
                
                # Continue processing other entries
                continue
        
        # Final summary
        self.stdout.write("=" * 60)
        self.stdout.write("📊 AI ANALYSIS COMPLETE")
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"📈 Results Summary:")
        self.stdout.write(f"   • Total processed: {processed}/{total_entries}")
        self.stdout.write(f"   • ✅ Successful: {successful}")
        self.stdout.write(f"   • ❌ Failed: {failed}")
        
        if successful > 0:
            success_rate = (successful / processed) * 100 if processed > 0 else 0
            self.stdout.write(f"   • 🎯 Success rate: {success_rate:.1f}%")
        
        # Show sample results
        if successful > 0:
            self.stdout.write("\n🔍 Sample Analysis Results:")
            sample_entries = PDFCodexEntry.objects.filter(
                ai_difficulty_score__isnull=False
            ).order_by('-ai_analyzed_at')[:5]
            
            for entry in sample_entries:
                self.stdout.write(
                    f"   ID {entry.id}: "
                    f"difficulty={entry.ai_difficulty_score:.2f}, "
                    f"category={entry.ai_category}, "
                    f"cognitive={entry.ai_cognitive_level}"
                )
        
        # Next steps
        self.stdout.write("\n🚀 Next Steps:")
        self.stdout.write("   1. Test the AI trivia system:")
        self.stdout.write("      GET /api/trivia/ai/question/")
        self.stdout.write("   2. Run migrations if needed:")
        self.stdout.write("      python manage.py makemigrations")
        self.stdout.write("      python manage.py migrate")
        self.stdout.write("   3. Check analysis quality in Django admin")
        
        if successful >= total_entries * 0.8:  # 80% success rate
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 AI analysis completed successfully! "
                    f"Your adaptive trivia system is ready to use."
                )
            )
        elif successful > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Partial success. Consider checking failed entries and rerunning analysis."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n❌ Analysis failed. Check your API configuration and content quality."
                )
            )
