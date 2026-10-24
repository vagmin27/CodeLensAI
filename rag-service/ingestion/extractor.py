import os
import re
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path


class DocumentExtractor:
    """
    Pure Python document ingestion and text extraction module.
    
    Responsible for:
    1. Validating file existence and supported formats (.txt, .md).
    2. Reading raw file contents with UTF-8 encoding (and graceful fallback).
    3. Normalizing whitespace and line endings without altering semantic content.
    4. Extracting key document metadata (size, word count, character count, hash ID).
    """

    SUPPORTED_EXTENSIONS = {".txt", ".md"}

    def __init__(self, supported_extensions: Optional[set] = None):
        self.supported_extensions = supported_extensions or self.SUPPORTED_EXTENSIONS

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a document from disk and extract its text and metadata.
        
        Args:
            file_path: Absolute or relative path to the document file.
            
        Returns:
            Dict containing document_id, filename, file_path, raw text content, and metadata.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is unsupported or file is empty.
        """
        path = Path(file_path).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file type '{path.suffix}'. "
                f"Supported types: {', '.join(sorted(self.supported_extensions))}"
            )

        # Read file with UTF-8, fallback to latin-1 if non-UTF-8 characters exist
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                raw_text = f.read()

        normalized_text = self._normalize_text(raw_text)

        if not normalized_text.strip():
            raise ValueError(f"Document at '{file_path}' is empty or contains only whitespace.")

        file_stat = path.stat()
        file_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()[:12]
        words = normalized_text.split()

        return {
            "document_id": f"doc_{file_hash}",
            "filename": path.name,
            "file_path": str(path),
            "content": normalized_text,
            "metadata": {
                "file_type": path.suffix.lower(),
                "file_size_bytes": file_stat.st_size,
                "character_count": len(normalized_text),
                "word_count": len(words),
                "checksum": file_hash,
            },
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Standardize line breaks to Unix style and collapse excessive blank lines.
        Preserves paragraph boundaries and intentional formatting.
        """
        # Convert Windows CRLF to standard LF
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace 3 or more consecutive newlines with 2 newlines (standard paragraph break)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
