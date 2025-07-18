from django.core.management.base import BaseCommand
from django.conf import settings
import json
import requests
from baybayin_wiki.services import WikiAPIService


class Command(BaseCommand):
    help = 'Test and sync data from external BaybayinWiki API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-only',
            action='store_true',
            help='Only test API connectivity without syncing data'
        )
        parser.add_argument(
            '--sync-categories',
            action='store_true',
            help='Sync categories from API'
        )
        parser.add_argument(
            '--sync-articles',
            action='store_true',
            help='Sync articles from API'
        )
        parser.add_argument(
            '--sync-timeline',
            action='store_true',
            help='Sync timeline events from API'
        )
        parser.add_argument(
            '--sync-glossary',
            action='store_true',
            help='Sync glossary terms from API'
        )
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help='Sync all data from API'
        )

    def handle(self, *args, **options):
        service = WikiAPIService()
        
        self.stdout.write(
            self.style.SUCCESS('🔗 Testing BaybayinWiki API Connection...')
        )
        
        # Test API connectivity
        connection_ok = self._test_api_connection()
        if not connection_ok:
            self.stdout.write(
                self.style.WARNING('⚠️ External API unavailable. Using fallback data.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ API connection successful!')
            )
        
        if options['test_only']:
            return
        
        # Sync data based on options (continue even if API is unavailable)
        if options['sync_all']:
            self._sync_all_data(service)
        else:
            if options['sync_categories']:
                self._sync_categories(service)
            if options['sync_articles']:
                self._sync_articles(service)
            if options['sync_timeline']:
                self._sync_timeline(service)
            if options['sync_glossary']:
                self._sync_glossary(service)

    def _test_api_connection(self):
        """Test basic API connectivity"""
        try:
            base_url = getattr(settings, 'WIKI_API_BASE_URL', '')
            if not base_url:
                self.stdout.write(
                    self.style.WARNING('⚠️ WIKI_API_BASE_URL not configured in settings')
                )
                return False
            
            # Test with a simple health check or categories endpoint
            response = requests.get(f"{base_url}/health", timeout=10)
            return response.status_code == 200
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Connection error: {str(e)}')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {str(e)}')
            )
            return False

    def _sync_categories(self, service):
        """Sync categories from API"""
        self.stdout.write('📁 Syncing categories...')
        try:
            result = service.sync_categories()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Categories synced: {result["synced"]} items')
            )
            if result.get('errors'):
                for error in result['errors']:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Warning: {error}')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Category sync failed: {str(e)}')
            )

    def _sync_articles(self, service):
        """Sync articles from API"""
        self.stdout.write('📄 Syncing articles...')
        try:
            result = service.sync_articles()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Articles synced: {result["synced"]} items')
            )
            if result.get('errors'):
                for error in result['errors']:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Warning: {error}')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Article sync failed: {str(e)}')
            )

    def _sync_timeline(self, service):
        """Sync timeline events from API"""
        self.stdout.write('⏰ Syncing timeline...')
        try:
            result = service.sync_timeline()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Timeline synced: {result["synced"]} items')
            )
            if result.get('errors'):
                for error in result['errors']:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Warning: {error}')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Timeline sync failed: {str(e)}')
            )

    def _sync_glossary(self, service):
        """Sync glossary terms from API"""
        self.stdout.write('📖 Syncing glossary...')
        try:
            result = service.sync_glossary()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Glossary synced: {result["synced"]} items')
            )
            if result.get('errors'):
                for error in result['errors']:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Warning: {error}')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Glossary sync failed: {str(e)}')
            )

    def _sync_all_data(self, service):
        """Sync all data from API"""
        self.stdout.write(
            self.style.SUCCESS('🔄 Starting full data synchronization...')
        )
        
        self._sync_categories(service)
        self._sync_articles(service)
        self._sync_timeline(service)
        self._sync_glossary(service)
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Full synchronization complete!')
        )
