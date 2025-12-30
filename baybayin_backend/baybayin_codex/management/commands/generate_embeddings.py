"""
Management command to generate embeddings for all CodexArticle entries.
Usage: python manage.py generate_embeddings
"""

from django.core.management.base import BaseCommand
from baybayin_codex.models import CodexArticle
from baybayin_codex.vector_store import BaybayinVectorStore
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Generates embeddings for all CodexArticle entries and stores them in FAISS index'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Generating embeddings for CodexArticle entries...'))
        
        # Initialize vector store
        index_path = os.path.join(settings.BASE_DIR, 'data', 'codex_vector_index.faiss')
        meta_path = os.path.join(settings.BASE_DIR, 'data', 'codex_vector_meta.pkl')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        vector_store = BaybayinVectorStore(index_path=index_path, meta_path=meta_path)
        
        # Clear existing index
        self.stdout.write('Clearing existing embeddings...')
        vector_store.clear()
        
        # Get all published articles
        articles = CodexArticle.objects.filter(is_published=True)
        
        if not articles.exists():
            self.stdout.write(self.style.WARNING('No published articles found!'))
            return
        
        self.stdout.write(f'Found {articles.count()} published articles')
        
        # Prepare texts and metadata
        texts = []
        meta_list = []
        
        for article in articles:
            # Combine title, summary, and content for better semantic search
            text = f"{article.title}\n\n{article.summary}\n\n{article.content}"
            texts.append(text)
            
            meta_list.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'category': article.category.name if article.category else 'Uncategorized',
                'tags': article.tags,
                'difficulty': article.difficulty,
                'url': article.url or '',
            })
        
        # Generate and store embeddings
        self.stdout.write('Generating embeddings (this may take a minute)...')
        vector_store.add_content(texts, meta_list)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully generated embeddings for {len(texts)} articles!'))
        self.stdout.write(self.style.SUCCESS(f'Index saved to: {index_path}'))
        self.stdout.write(self.style.SUCCESS('The chat feature is now ready to use!'))
