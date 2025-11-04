"""
Django Management Command: Scrape Baybayin Wiki Content

This command scrapes content from Wikipedia and cultural institutions,
enhances it for educational quality, and saves it to the database.

Usage:
    python manage.py scrape_wiki_content [--force] [--clean] [--sources wikipedia,cultural]
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from baybayin_codex.services import WikiContentService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape and update Baybayin wiki content from external sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh content regardless of last update time'
        )
        
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing scraped content before updating'
        )
        
        parser.add_argument(
            '--sources',
            type=str,
            default='wikipedia,cultural',
            help='Comma-separated list of sources to scrape (wikipedia,cultural)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform scraping without saving to database'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        
        if self.verbose:
            logging.basicConfig(level=logging.DEBUG)
        
        self.stdout.write(
            self.style.SUCCESS('Starting Baybayin Wiki Content Scraping...')
        )
        
        try:
            # Initialize service
            wiki_service = WikiContentService()
            
            # Show current content status
            self._show_content_status(wiki_service)
            
            # Clean existing content if requested
            if options['clean']:
                self._clean_existing_content(wiki_service)
            
            # Perform scraping and update
            if not options['dry_run']:
                result = wiki_service.scrape_and_update_content(
                    force_refresh=options['force']
                )
                self._display_results(result)
            else:
                self.stdout.write(
                    self.style.WARNING('Dry run mode - no content will be saved')
                )
                # Just show what would be scraped
                scraped_data = wiki_service._scrape_all_sources()
                self._display_dry_run_results(scraped_data)
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.ERROR('Operation cancelled by user')
            )
            return
        except Exception as e:
            logger.exception("Command execution failed")
            raise CommandError(f'Scraping failed: {str(e)}')
    
    def _show_content_status(self, wiki_service):
        """Show current content status"""
        self.stdout.write('\nCurrent Content Status:')
        
        try:
            stats = wiki_service.content_manager.get_content_statistics()
            freshness = wiki_service.get_content_freshness_status()
            
            self.stdout.write(f"   Articles: {stats['articles']['total']} "
                            f"(Featured: {stats['articles']['featured']})")
            self.stdout.write(f"   Categories: {stats['categories']['total']} "
                            f"(Featured: {stats['categories']['featured']})")
            self.stdout.write(f"   Timeline Events: {stats['timeline']['total']}")
            self.stdout.write(f"   Glossary Terms: {stats['glossary']['total']}")
            
            # Content freshness
            status_colors = {
                'never_scraped': self.style.ERROR,
                'very_fresh': self.style.SUCCESS,
                'fresh': self.style.SUCCESS,
                'aging': self.style.WARNING,
                'stale': self.style.ERROR
            }
            
            status_color = status_colors.get(freshness['status'], self.style.NOTICE)
            self.stdout.write(f"   Content Status: {status_color(freshness['status'].upper())}")
            
            if freshness.get('last_scraping'):
                self.stdout.write(f"   Last Scraping: {freshness['last_scraping']}")
                self.stdout.write(f"   Hours Since Last: {freshness['hours_since_last']}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting content status: {e}')
            )
    
    def _clean_existing_content(self, wiki_service):
        """Clean existing scraped content"""
        self.stdout.write('\nCleaning existing scraped content...')
        
        try:
            result = wiki_service.content_manager.clean_existing_content()
            
            if result['success']:
                deleted = result.get('deleted_counts', {})
                self.stdout.write(self.style.SUCCESS(
                    f"Cleaned content: "
                    f"Articles: {deleted.get('articles', 0)}, "
                    f"Timeline: {deleted.get('timeline', 0)}, "
                    f"Glossary: {deleted.get('glossary', 0)}"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"Content cleaning failed: {result.get('error', 'Unknown error')}"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cleaning content: {e}'))
    
    def _display_results(self, result):
        """Display scraping and update results"""
        self.stdout.write('\nScraping Results:')
        
        if result['success']:
            self.stdout.write(self.style.SUCCESS('Content scraping completed successfully!'))
            
            # Display save statistics
            save_result = result.get('save_result', {})
            if save_result.get('stats'):
                stats = save_result['stats']
                self.stdout.write('\nContent Statistics:')
                
                for content_type in ['categories', 'articles', 'timeline', 'glossary']:
                    created = stats.get('created', {}).get(content_type, 0)
                    updated = stats.get('updated', {}).get(content_type, 0)
                    errors = stats.get('errors', {}).get(content_type, 0)
                    
                    if created > 0 or updated > 0 or errors > 0:
                        self.stdout.write(
                            f"   {content_type.title()}: "
                            f"Created: {created}, Updated: {updated}, Errors: {errors}"
                        )
            
            # Display quality report
            quality_report = result.get('quality_report', {})
            if quality_report:
                self.stdout.write('\nQuality Report:')
                self.stdout.write(f"   Total Articles: {quality_report.get('total_articles', 0)}")
                self.stdout.write(f"   Featured Articles: {quality_report.get('featured_articles', 0)}")
                self.stdout.write(f"   High Quality Articles: {quality_report.get('high_quality_articles', 0)}")
                self.stdout.write(f"   Overall Score: {quality_report.get('overall_score', 0):.2f}")
            
            # Display completion time
            completed_at = result.get('scraping_completed_at', '')
            if completed_at:
                self.stdout.write(f"\nCompleted at: {completed_at}")
        else:
            self.stdout.write(self.style.ERROR(
                f"Content scraping failed: {result.get('error', 'Unknown error')}"
            ))
    
    def _display_dry_run_results(self, scraped_data):
        """Display dry run results"""
        self.stdout.write('\nDry Run Results (Content that would be scraped):')
        
        for content_type, items in scraped_data.items():
            count = len(items) if items else 0
            self.stdout.write(f"   {content_type.replace('_', ' ').title()}: {count} items")
            
            if self.verbose and items and count > 0:
                self.stdout.write(f"     Sample items:")
                for i, item in enumerate(items[:3]):  # Show first 3 items
                    if content_type == 'articles':
                        title = item.get('title', 'No title')[:50]
                        self.stdout.write(f"     - {title}...")
                    elif content_type == 'glossary_terms':
                        term = item.get('term', 'No term')
                        self.stdout.write(f"     - {term}")
                    elif content_type == 'timeline_events':
                        title = item.get('title', 'No title')[:50]
                        date = item.get('date', 'No date')
                        self.stdout.write(f"     - {date}: {title}...")
                    elif content_type == 'categories':
                        name = item.get('name', 'No name')
                        self.stdout.write(f"     - {name}")
                        
                if count > 3:
                    self.stdout.write(f"     ... and {count - 3} more")
        
        self.stdout.write('\nTip: Use --verbose for more detailed output')
        self.stdout.write('Tip: Remove --dry-run to actually save content to database')
