import fitz
from pathlib import Path

def extract_pdf_images(pdf_path, out_dir):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)

    image_paths = []

    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        fp = f"{out_dir}/page_{i+1}.png"
        pix.save(fp)
        image_paths.append(fp)

    return image_paths
