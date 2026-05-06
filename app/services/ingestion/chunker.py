def chunk_text(raw_text: str, max_chars: int = 900) -> list[str]:
    """Simple paragraph-aware chunker for local demos.

    TODO: Replace with token-aware, document-type-aware chunking. Code chunks should preserve
    function/class boundaries; Markdown chunks should preserve headings; logs should preserve
    timestamps and trace IDs.
    """
    paragraphs = [part.strip() for part in raw_text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs or [raw_text.strip()]:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current.strip():
        chunks.append(current.strip())
    return chunks
