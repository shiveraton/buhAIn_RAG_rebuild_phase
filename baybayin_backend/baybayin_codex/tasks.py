from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def scrape_codex_content_periodic():
    try:
        call_command('scrape_codex_content', verbosity=1, force=True)
        logger.info("Periodic codex scraping completed successfully")
        return "Scraping completed"
    except Exception as e:
        logger.error(f"Periodic scraping failed: {e}")
        return f"Scraping failed: {e}"