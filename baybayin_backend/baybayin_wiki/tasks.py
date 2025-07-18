from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def scrape_wiki_content_periodic():
    try:
        call_command('scrape_wiki_content', verbosity=1, force=True)
        logger.info("Periodic wiki scraping completed successfully")
        return "Scraping completed"
    except Exception as e:
        logger.error(f"Periodic scraping failed: {e}")
        return f"Scraping failed: {e}"