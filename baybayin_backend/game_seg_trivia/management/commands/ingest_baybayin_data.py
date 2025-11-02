import os
import json
import uuid
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from sentence_transformers import SentenceTransformer

# Import the real models
from game_seg_trivia.models import TriviaSourceFact, TriviaArchive

# --- Mock Text File for Testing ---
MOCK_SOURCE_FILE = 'baybayin_mock_source.txt'

# --- Configuration ---
ARCHIVE_TITLE = "Baybayin Reference Book"
EMBEDDING_MODEL = 'monsoon-nlp/monsoon-paraphrase-filipino'
EMBEDDING_DIMENSION = 768  # monsoon-paraphrase-filipino dimension
embedder = SentenceTransformer(EMBEDDING_MODEL)

# --- Embedding client - uses real SentenceTransformer with monsoon-paraphrase-filipino ---
def get_embedding_client():
    """
    Returns an embedding client for generating embeddings using monsoon-paraphrase-filipino
    """
    class SentenceTransformerClient:
        def __init__(self, model):
            self.model = model
        
        def embed_text(self, text):
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
    
    return SentenceTransformerClient(embedder)

class Command(BaseCommand):
    help = 'Ingests and embeds Baybayin source material into pgvector in one streamlined command.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=MOCK_SOURCE_FILE,
            help=f'Path to the concatenated raw source text file (OCR output). Default: {MOCK_SOURCE_FILE}'
        )
        parser.add_argument(
            '--archive-id',
            type=str,
            help='Optional: The ID of an existing TriviaArchive to link chunks to.'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        archive_id = options.get('archive_id')

        # 1. Simulate OCR Output Access
        self.stdout.write(f"1. Reading source text from: {file_path}")
        try:
            raw_text = Path(file_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            raise CommandError(f"File not found at {file_path}. Please create the mock file.")
        
        if not raw_text.strip():
            self.stdout.write(self.style.WARNING("Source text is empty. Aborting."))
            return

        # 2. Setup Archive (Source Metadata)
        if archive_id:
            try:
                archive = TriviaArchive.objects.get(pk=archive_id)
            except TriviaArchive.DoesNotExist:
                raise CommandError(f"TriviaArchive with ID {archive_id} not found.")
        else:
            archive, created = TriviaArchive.objects.get_or_create(
                title=ARCHIVE_TITLE,
                defaults={'source_type': 'book', 'debug_file_path': 'temp/debug_file.txt'} # Example defaults
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new Archive: {archive.title} (ID: {archive.id})"))
            else:
                self.stdout.write(self.style.NOTICE(f"Using existing Archive: {archive.title} (ID: {archive.id})"))
        
        # NOTE on Debugging File: The final, cleaned raw_text string should be saved here 
        # for debugging the OCR/cleaning step, as per our discussion.

        # 3. Chunking (Medium-sized, Paragraph-based)
        self.stdout.write("2. Performing heuristic chunking (paragraph breaks)...")
        chunks = self.chunk_text_by_paragraph(raw_text)
        self.stdout.write(f"   -> Generated {len(chunks)} chunks.")

        # 4. Embedding and Database Persistence
        self.stdout.write("3. Embedding and persisting chunks to pgvector...")
        embedding_client = get_embedding_client()
        total_chunks = len(chunks)
        
        with transaction.atomic():
            # Clear old facts related to this archive to prevent duplicates
            TriviaSourceFact.objects.filter(source_archive=archive).delete()
            self.stdout.write(f"   -> Cleared existing facts for Archive ID {archive.id}.")
            
            for i, chunk_text in enumerate(chunks):
                self.stdout.write(f"   -> Processing chunk {i+1}/{total_chunks}", ending='\r')

                try:
                    # a. Generate Embedding
                    embedding_vector = embedding_client.embed_text(chunk_text)
                    
                    # b. Determine Page/Chapter Metadata (Heuristic/Mock)
                    # NOTE: In a real-world scenario, this metadata would come from the OCR/cleaning script
                    # that knows the page number when it extracts the text. Here, it's mocked:
                    page_number = (i // 5) + 1 # Assigns a page every 5 chunks
                    
                    # c. Create Database Entry
                    TriviaSourceFact.objects.create(
                        content=chunk_text,
                        embedding=embedding_vector,
                        token_count=len(chunk_text.split()), # Mock token count
                        source_archive=archive,
                        metadata=json.dumps({
                            'page': page_number,
                            'chapter': 'Linguistic Rules' if page_number < 3 else 'Historical Context'
                        })
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"\n   -> FAILED to process chunk {i+1}: {e}"))
                    # Continue to next chunk or raise fatal error based on policy

        self.stdout.write(self.style.SUCCESS(f"\n4. Successfully ingested and embedded {total_chunks} facts."))
        self.stdout.write(self.style.SUCCESS("Data Pipeline Complete. The RAG system is now primed for retrieval."))

    def chunk_text_by_paragraph(self, raw_text):
        """
        Splits text by double newlines (paragraph breaks) and filters out empty lines.
        This implements the agreed-upon medium-sized, semantic chunking strategy.
        """
        # Replace common variations of double breaks with a standard one
        cleaned_text = raw_text.replace('\r\n\r\n', '\n\n').replace('\r\r', '\n\n')
        
        # Split by double newline (paragraph)
        chunks = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]

        # Fallback for very long chunks (e.g., if the source has no paragraph breaks)
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > 1000: # Example of a token/character limit check (approx 512 tokens)
                # Simple split for the too-long chunk
                sub_chunks = [chunk[i:i + 800] for i in range(0, len(chunk), 800)]
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks