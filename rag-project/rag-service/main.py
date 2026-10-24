import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path to allow clean absolute imports within rag-service
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Set standard output encoding to utf-8 if supported on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ingestion.extractor import DocumentExtractor
from chunking.chunker import TextChunker


def run_pipeline(file_path: str, chunk_size: int, chunk_overlap: int, inspect_count: int, output_json: bool):
    """
    Executes Document Ingestion, Text Extraction, and Overlapping Chunking.
    """
    extractor = DocumentExtractor()
    chunker = TextChunker(default_chunk_size=chunk_size, default_chunk_overlap=chunk_overlap)

    # 1. Ingestion & Extraction
    print("\n" + "=" * 65)
    print(" [CodeLens AI] Phase 1 - Milestone 1: Ingestion & Chunking")
    print("=" * 65)
    print(f"\n[1/2] Ingesting & Extracting: {file_path}")
    
    try:
        document = extractor.extract(file_path)
    except Exception as e:
        print(f"Extraction Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  [+] Document ID     : {document['document_id']}")
    print(f"  [+] Source File     : {document['filename']}")
    print(f"  [+] File Size       : {document['metadata']['file_size_bytes']} bytes")
    print(f"  [+] Total Words     : {document['metadata']['word_count']} words")
    print(f"  [+] Character Count : {document['metadata']['character_count']} characters")

    # 2. Overlapping Chunking
    print(f"\n[2/2] Generating Sliding-Window Chunks (Size: {chunk_size} words, Overlap: {chunk_overlap} words)...")
    try:
        chunks = chunker.chunk_document(document, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    except Exception as e:
        print(f"Chunking Error: {e}", file=sys.stderr)
        sys.exit(1)

    stride = chunk_size - chunk_overlap
    print(f"  [+] Total Chunks Generated : {len(chunks)}")
    print(f"  [+] Window Stride (Step)   : {stride} words")

    if output_json:
        result = {
            "document": document,
            "chunks": chunks
        }
        print(json.dumps(result, indent=2))
        return

    # Visual Inspection of Chunks
    display_limit = min(inspect_count, len(chunks))
    print(f"\n--- Detailed Inspection of First {display_limit} Chunk(s) ---")
    
    for i in range(display_limit):
        chunk = chunks[i]
        print(f"\n>>> [Chunk {chunk['chunk_index']} | ID: {chunk['chunk_id']}]")
        print(f"    Words: {chunk['word_count']} | Chars: {chunk['char_length']} | Offset: [{chunk['start_char']}:{chunk['end_char']}]")
        print(f"    Content Preview:")
        
        # Display the text with neat indentation
        lines = chunk['text'].split('\n')
        for line in lines:
            print(f"      {line}")

        # Highlight overlap with the next chunk if applicable
        if i + 1 < len(chunks):
            current_words = chunk['text'].split()
            next_words = chunks[i + 1]['text'].split()
            overlapping = current_words[-chunk_overlap:] if len(current_words) >= chunk_overlap else current_words
            overlap_text = " ".join(overlapping)
            print(f"    --> Overlap with Chunk {i+1} ({len(overlapping)} words):")
            print(f"        \"{overlap_text}\"")

    print("\n" + "=" * 65)
    print(" Pipeline Milestone 1 Execution Successful.")
    print(" Ready for Milestone 2: Embedding Generation & Storage.")
    print("=" * 65 + "\n")


def main():
    default_doc = current_dir / "sample_docs" / "nodejs_event_loop.md"
    
    parser = argparse.ArgumentParser(
        description="CodeLens AI - Pure Python RAG Ingestion & Chunking Pipeline"
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        default=str(default_doc),
        help=f"Path to document file (.txt or .md). Defaults to {default_doc.name}"
    )
    parser.add_argument(
        "-s", "--chunk-size",
        type=int,
        default=50,
        help="Chunk size in number of words (default: 50)"
    )
    parser.add_argument(
        "-o", "--chunk-overlap",
        type=int,
        default=15,
        help="Chunk overlap in number of words (default: 15)"
    )
    parser.add_argument(
        "-i", "--inspect",
        type=int,
        default=3,
        help="Number of chunks to display in detail (default: 3)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full document and chunks as JSON"
    )

    args = parser.parse_args()
    run_pipeline(
        file_path=args.file,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        inspect_count=args.inspect,
        output_json=args.json
    )


if __name__ == "__main__":
    main()
