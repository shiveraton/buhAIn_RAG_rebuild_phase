"""
Quick setup script to populate test data for Postman testing
Run this to create sample content for API testing
"""

from django.core.management.base import BaseCommand
from baybayin_codex.models import CodexCategory, CodexArticle, CodexTimeline, CodexGlossary
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create sample data for API testing'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data for BaybayinCodex API testing...")
        
        # Create categories
        history_cat, created = CodexCategory.objects.get_or_create(
            name="History",
            defaults={
                'description': 'Historical content about Baybayin',
                'icon': 'time',
                'color': '#ff6b35',
                'order': 1
            }
        )
        
    script_cat, created = CodexCategory.objects.get_or_create(
            name="Script & Writing",
            defaults={
                'description': 'Information about Baybayin script',
                'icon': 'create',
                'color': '#3880ff',
                'order': 2
            }
        )
        
    culture_cat, created = CodexCategory.objects.get_or_create(
            name="Culture",
            defaults={
                'description': 'Cultural aspects of Baybayin',
                'icon': 'people',
                'color': '#10dc60',
                'order': 3
            }
        )
        
        # Create sample articles
    article1, created = CodexArticle.objects.get_or_create(
            title="Introduction to Baybayin",
            defaults={
                'category': script_cat,
                'summary': 'Learn the basics of the ancient Filipino script',
                'content': '<p>Baybayin is a pre-colonial Philippine writing system that was used to write various Filipino languages...</p>',
                'difficulty_level': 'beginner',
                'tags': ['basics', 'introduction', 'script'],
                'source': 'manual',
                'is_published': True,
                'is_featured': True,
                'reading_time': 5
            }
        )
        
    article2, created = CodexArticle.objects.get_or_create(
            title="History of Baybayin",
            defaults={
                'category': history_cat,
                'summary': 'Explore the rich history of Filipino writing',
                'content': '<p>The history of Baybayin dates back to the pre-colonial period...</p>',
                'difficulty_level': 'intermediate',
                'tags': ['history', 'pre-colonial', 'Philippines'],
                'source': 'manual',
                'is_published': True,
                'reading_time': 8
            }
        )
        
        # Create timeline events
    CodexTimeline.objects.get_or_create(
            title="First documented use of Baybayin",
            defaults={
                'year': 900,
                'period': 'Pre-colonial',
                'description': 'The Laguna Copperplate Inscription, the earliest known written document in the Philippines',
                'importance': 'critical',
                'source': 'historical_records'
            }
        )
        
    CodexTimeline.objects.get_or_create(
            title="Spanish colonization begins",
            defaults={
                'year': 1565,
                'period': 'Spanish Era',
                'description': 'The Spanish began their colonization, gradually replacing Baybayin with Latin script',
                'importance': 'high',
                'source': 'historical_records'
            }
        )
        
        # Create glossary terms
    CodexGlossary.objects.get_or_create(
            term="Baybayin",
            defaults={
                'definition': 'Ancient Filipino script used before Spanish colonization',
                'category': 'Script',
                'difficulty_level': 'beginner',
                'source': 'manual'
            }
        )
        
    CodexGlossary.objects.get_or_create(
            term="Alibata",
            defaults={
                'definition': 'Incorrect term sometimes used to refer to Baybayin',
                'category': 'Script',
                'difficulty_level': 'intermediate',
                'source': 'manual'
            }
        )
        
    CodexGlossary.objects.get_or_create(
            term="Kudlit",
            defaults={
                'definition': 'Diacritical marks used in Baybayin to modify vowel sounds',
                'category': 'Script',
                'difficulty_level': 'advanced',
                'source': 'manual'
            }
        )
        
    self.stdout.write(
        self.style.SUCCESS('Successfully created sample data for API testing!')
    )
    self.stdout.write(f"Categories: {CodexCategory.objects.count()}")
    self.stdout.write(f"Articles: {CodexArticle.objects.count()}")
    self.stdout.write(f"Timeline events: {CodexTimeline.objects.count()}")
    self.stdout.write(f"Glossary terms: {CodexGlossary.objects.count()}")
