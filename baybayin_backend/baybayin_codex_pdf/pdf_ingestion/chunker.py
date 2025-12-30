def chunk_text(text, min_len=40):
    blocks = []
    for part in text.split("\n\n"):
        clean = part.strip()
        if len(clean) >= min_len:
            blocks.append(clean)
    return blocks
