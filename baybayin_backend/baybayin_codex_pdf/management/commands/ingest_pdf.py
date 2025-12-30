import os
import fitz
import pytesseract
from tqdm import tqdm
import numpy as np
import cv2
from baybayin_codex_pdf.models import PDFCodexEntry
from game_seg_trivia.retrieval_service import get_embedding_model
from django.core.management.base import BaseCommand

# Optional: configure Tesseract path if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def split_text_into_chunks(text, max_chars=500):
    """Split text into chunks of up to max_chars characters"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end
    return chunks

def ocr_image(pix):
    """Convert PyMuPDF pixmap to grayscale + thresholding and OCR"""
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(thresh, lang="tgl+eng").strip()
    return text

class Command(BaseCommand):
    help = "Ingest scanned PDF into PDFCodexEntry with improved OCR"

    def add_arguments(self, parser):
        parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
        parser.add_argument("--min_length", type=int, default=40, help="Minimum characters to save per chunk")
        parser.add_argument("--chunk_size", type=int, default=500, help="Maximum characters per chunk")

    def handle(self, *args, **options):
        pdf_path = options["pdf_path"]
        min_length = options["min_length"]
        chunk_size = options["chunk_size"]

        if not os.path.exists(pdf_path):
            self.stderr.write(f"PDF not found: {pdf_path}")
            return

        doc = fitz.open(pdf_path)
        model = get_embedding_model()
        inserted_count = 0

        self.stdout.write(f"Ingesting {len(doc)} pages from {pdf_path}...")

        for page_num in tqdm(range(len(doc))):
            page = doc[page_num]
            
            # Extract text if available
            text = page.get_text().strip()
            
            # If no text, run OCR with preprocessing
            if not text:
                pix = page.get_pixmap()
                text = ocr_image(pix)
                if not text:
                    self.stderr.write(f"OCR failed on page {page_num + 1}")

            if len(text) < min_length:
                continue

            # Split into chunks
            chunks = split_text_into_chunks(text, max_chars=chunk_size)
            
            for chunk_idx, chunk_text in enumerate(chunks):
                if len(chunk_text.strip()) < min_length:
                    continue

                try:
                    embedding = model.encode([chunk_text])[0].tolist()
                except Exception as e:
                    self.stderr.write(f"Failed embedding page {page_num + 1} chunk {chunk_idx}: {e}")
                    continue

                PDFCodexEntry.objects.create(
                    text=chunk_text,
                    embedding=embedding,
                    page_number=page_num + 1,
                    chunk_index=chunk_idx
                )
                inserted_count += 1

        self.stdout.write(self.style.SUCCESS(f"Inserted {inserted_count} PDF entries into PDFCodexEntry"))
