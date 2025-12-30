from pdf_ingestion.extractor import extract_pdf_images
from pdf_ingestion.preprocess import preprocess_image
from pdf_ingestion.ocr import run_ocr
from pdf_ingestion.chunker import chunk_text
from baybayin_codex_pdf.models import PDFCodexEntry
from game_seg_trivia.retrieval_service import get_embedding_model

import cv2

def ingest(pdf_path):
    model = get_embedding_model()
    
    images = extract_pdf_images(pdf_path, out_dir="tmp_pdf_pages")

    for idx, img_path in enumerate(images):
        img = preprocess_image(img_path)
        text = run_ocr(img)
        chunks = chunk_text(text)

        for ci, chunk in enumerate(chunks):
            embedding = model.encode([chunk])[0].tolist()
            
            PDFCodexEntry.objects.create(
                text=chunk,
                cleaned_text=chunk,
                embedding=embedding,
                page_number=idx + 1,
                chunk_index=ci
            )

    print("PDF ingestion completed.")
