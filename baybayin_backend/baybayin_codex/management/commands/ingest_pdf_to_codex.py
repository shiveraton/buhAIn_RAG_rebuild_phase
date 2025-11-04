"""
Management command to ingest Baybayin PDF book into the codex (CodexArticle + TriviaSourceFact).
Uses PDFAnalyzer, monsoon-paraphrase-filipino embeddings, and heuristic chunking.
"""
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from sentence_transformers import SentenceTransformer
import re

from baybayin_codex.models import CodexArticle, CodexCategory
from baybayin_codex.analyzer.pdf_analyzer import PDFAnalyzer
from game_seg_trivia.models import TriviaSourceFact, TriviaArchive

# Configuration
PDF_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'baybayin_codex' / 'book' / 'munting_aklat_baybayin.pdf'
EMBEDDING_MODEL = 'monsoon-nlp/monsoon-paraphrase-filipino'
EMBEDDING_DIMENSION = 768
CHUNK_MAX_WORDS = 500
CHUNK_MIN_WORDS = 50


class Command(BaseCommand):
    help = 'Ingest Baybayin PDF book into CodexArticle and TriviaSourceFact for RAG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf-path',
            type=str,
            default=str(PDF_PATH),
            help='Path to the Baybayin PDF book'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing CodexArticles and TriviaSourceFacts before ingestion'
        )

    def handle(self, *args, **options):
        pdf_path = Path(options['pdf_path'])
        clear_existing = options['clear_existing']

        # Validate PDF exists
        if not pdf_path.exists():
            raise CommandError(f"PDF file not found: {pdf_path}")

        self.stdout.write(self.style.SUCCESS(f"Starting PDF ingestion from: {pdf_path}"))

        # Step 1: Extract text from PDF
        self.stdout.write("1. Extracting text from PDF...")
        analyzer = PDFAnalyzer(str(pdf_path))
        full_text = analyzer.extract_text()
        
        if not full_text:
            raise CommandError("Failed to extract text from PDF. PDF might be image-based (needs OCR).")
        
        self.stdout.write(self.style.SUCCESS(f"   Extracted {len(full_text)} characters"))

        # Step 2: Chunk the text
        self.stdout.write("2. Chunking text into articles...")
        chunks = self._chunk_text(full_text)
        self.stdout.write(self.style.SUCCESS(f"   Created {len(chunks)} chunks"))

        # Step 3: Load embedding model
        self.stdout.write("3. Loading embedding model (monsoon-paraphrase-filipino)...")
        try:
            embedder = SentenceTransformer(EMBEDDING_MODEL)
            self.stdout.write(self.style.SUCCESS(f"   Model loaded: {EMBEDDING_MODEL}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Failed to load {EMBEDDING_MODEL}: {e}"))
            self.stdout.write("   Falling back to all-MiniLM-L6-v2...")
            embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Step 4: Clear existing data if requested
        if clear_existing:
            self.stdout.write("4. Clearing existing data...")
            with transaction.atomic():
                CodexArticle.objects.filter(source='munting_aklat_baybayin').delete()
                TriviaSourceFact.objects.filter(source_archive__title='Munting Aklat ng Baybayin').delete()
        self.stdout.write(self.style.SUCCESS("   Cleared existing records"))

    # Step 5: Get or create category and archive
    self.stdout.write("5. Setting up category and archive...")
    category, _ = CodexCategory.objects.get_or_create(
        name='Baybayin History',
        defaults={
            'description': 'Historical context and evolution of Baybayin script',
            'icon': 'book-outline',
            'color': '#8B4513'
        }
    )
    
    archive, _ = TriviaArchive.objects.get_or_create(
        title='Munting Aklat ng Baybayin',
        defaults={
            'source': 'munting_aklat_baybayin.pdf',
            'metadata': {'ingestion_version': '1.0'}
        }
    )

    # Step 6: Process chunks and create database entries
    self.stdout.write("6. Creating CodexArticles and TriviaSourceFacts...")
    created_articles = 0
    created_facts = 0

    with transaction.atomic():
        for idx, chunk in enumerate(chunks):
            # Generate title from first sentence or heading
            title = self._extract_title(chunk, idx)
            
            # Generate embedding
            embedding = embedder.encode([chunk])[0].tolist()

            # Create CodexArticle
            article = CodexArticle.objects.create(
                title=title,
                content=chunk,
                summary=chunk[:200] + '...' if len(chunk) > 200 else chunk,
                category=category,
                difficulty='medium',
                source='munting_aklat_baybayin',
                tags=['baybayin', 'history', 'philippine-script'],
                metadata={
                    'chunk_index': idx,
                    'word_count': len(chunk.split()),
                    'embedding_model': EMBEDDING_MODEL
                }
            )
            created_articles += 1

            # Create TriviaSourceFact
            TriviaSourceFact.objects.create(
                text_content=chunk,
                source_archive=archive,
                metadata={
                    'codex_article_id': article.id,
                    'chunk_index': idx,
                    'title': title
                },
                embedding=embedding
            )
            created_facts += 1

        if (idx + 1) % 10 == 0:
            self.stdout.write(f"   Processed {idx + 1}/{len(chunks)} chunks", ending='\r')

    self.stdout.write(self.style.SUCCESS(f"\n✅ Ingestion complete!"))
    self.stdout.write(self.style.SUCCESS(f"   Created {created_articles} CodexArticles"))
    self.stdout.write(self.style.SUCCESS(f"   Created {created_facts} TriviaSourceFacts"))
    self.stdout.write(self.style.SUCCESS(f"   Category: {category.name}"))
    self.stdout.write(self.style.SUCCESS(f"   Archive: {archive.title}"))

    def _chunk_text(self, text: str) -> list[str]:
        """
        Chunk text into logical sections using heuristic paragraph-based splitting.
        Aims for chunks between CHUNK_MIN_WORDS and CHUNK_MAX_WORDS.
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        chunks = []
        current_chunk = []
        current_word_count = 0

        for para in paragraphs:
            para_word_count = len(para.split())
            
            # If adding this paragraph keeps us under max, add it
            if current_word_count + para_word_count <= CHUNK_MAX_WORDS:
                current_chunk.append(para)
                current_word_count += para_word_count
            else:
                # Save current chunk if it meets minimum
                if current_word_count >= CHUNK_MIN_WORDS:
                    chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with current paragraph
                current_chunk = [para]
                current_word_count = para_word_count

        # Add final chunk
        if current_chunk and current_word_count >= CHUNK_MIN_WORDS:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _extract_title(self, chunk: str, idx: int) -> str:
        """
        Extract a title from the chunk's first sentence or generate one.
        """
        # Try to find a heading pattern (all caps, short line, etc.)
        lines = chunk.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and len(line) < 80 and (line.isupper() or line.istitle()):
                return line

        # Otherwise use first sentence (up to 80 chars)
        first_sentence = chunk.split('.')[0].strip()
        if len(first_sentence) > 80:
            first_sentence = first_sentence[:77] + '...'
        
        return first_sentence or f"Baybayin History - Section {idx + 1}"