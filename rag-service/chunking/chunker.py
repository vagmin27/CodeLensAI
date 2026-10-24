import re
from typing import List, Dict, Any, Optional


class TextChunker:
    """
    Pure Python sliding-window text chunker with configurable size and overlap.
    
    Why chunking is needed in RAG:
    1. LLM Context Windows: Sending an entire document is expensive and can exceed token limits.
    2. Retrieval Granularity: Smaller, focused chunks create sharper vector embeddings,
       making it much easier to match the exact paragraph answering a user's question.
    3. Overlap Rationale: Overlap ensures concepts or sentences split across chunk boundaries
       are not severed from their surrounding context, avoiding information loss.
    """

    def __init__(self, default_chunk_size: int = 60, default_chunk_overlap: int = 15):
        """
        Args:
            default_chunk_size: Target number of words per chunk.
            default_chunk_overlap: Number of overlapping words between consecutive chunks.
        """
        self._validate_params(default_chunk_size, default_chunk_overlap)
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap

    @staticmethod
    def _validate_params(chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

    def chunk_text(
        self,
        text: str,
        document_id: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Splits raw text into overlapping word-based chunks while tracking character offsets.
        
        Args:
            text: Raw or normalized text content.
            document_id: Identifier of the parent document.
            chunk_size: Optional override for words per chunk.
            chunk_overlap: Optional override for overlapping words.
            
        Returns:
            List of chunk dictionaries with metadata and character boundary offsets.
        """
        size = chunk_size if chunk_size is not None else self.default_chunk_size
        overlap = chunk_overlap if chunk_overlap is not None else self.default_chunk_overlap
        self._validate_params(size, overlap)

        text = text.strip()
        if not text:
            return []

        # Find all words with their start and end character positions in the original text
        word_matches = list(re.finditer(r"\S+", text))
        total_words = len(word_matches)

        if total_words == 0:
            return []

        step = size - overlap
        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for start_idx in range(0, total_words, step):
            end_idx = min(start_idx + size, total_words)
            slice_matches = word_matches[start_idx:end_idx]

            start_char = slice_matches[0].start()
            end_char = slice_matches[-1].end()
            chunk_text = text[start_char:end_char]

            chunk_obj = {
                "chunk_id": f"{document_id}_chunk_{chunk_index}",
                "chunk_index": chunk_index,
                "text": chunk_text,
                "word_count": len(slice_matches),
                "char_length": len(chunk_text),
                "start_char": start_char,
                "end_char": end_char,
                "metadata": {
                    "source_document_id": document_id,
                    "chunk_size": size,
                    "chunk_overlap": overlap,
                    "is_first_chunk": (chunk_index == 0),
                    "is_last_chunk": (end_idx >= total_words),
                },
            }
            chunks.append(chunk_obj)
            chunk_index += 1

            if end_idx >= total_words:
                break

        return chunks

    def chunk_document(
        self,
        document: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper to chunk an extracted document dict.
        Attaches the source filename to each chunk's metadata.
        """
        chunks = self.chunk_text(
            text=document["content"],
            document_id=document["document_id"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk in chunks:
            chunk["metadata"]["source_filename"] = document["filename"]

        return chunks
