from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    chunk_id: int
    total_chunks: int
    char_start: int
    char_end: int


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[TextChunk]:
    """
    Split text into overlapping chunks. Snaps to word boundaries so we
    never cut a word in half. Returns an empty list for blank input.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [TextChunk(text=text, chunk_id=0, total_chunks=1, char_start=0, char_end=len(text))]

    step = chunk_size - overlap
    chunks: list[TextChunk] = []
    chunk_id = 0
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Snap to word boundary (don't cut mid-word) unless we're at the end
        if end < len(text):
            snap = text.rfind(" ", start, end)
            if snap > start:
                end = snap

        chunk_text_str = text[start:end].strip()
        if chunk_text_str:
            chunks.append(
                TextChunk(
                    text=chunk_text_str,
                    chunk_id=chunk_id,
                    total_chunks=0,  # filled below
                    char_start=start,
                    char_end=end,
                )
            )
            chunk_id += 1

        start += step

    total = len(chunks)
    for chunk in chunks:
        chunk.total_chunks = total

    return chunks
