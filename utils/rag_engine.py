"""Chroma-backed RAG over CodersGuild PDFs and indexed code snippets."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from utils.logger import setup_logger

try:
    import chromadb
    from chromadb.config import Settings
except ImportError as exc:
    chromadb = None  # type: ignore[assignment]
    Settings = None  # type: ignore[misc, assignment]
    _CHROMA_IMPORT_ERROR = exc
else:
    _CHROMA_IMPORT_ERROR = None

try:
    from pypdf import PdfReader
except ImportError as exc:
    PdfReader = None  # type: ignore[misc, assignment]
    _PDF_IMPORT_ERROR = exc
else:
    _PDF_IMPORT_ERROR = None


class RAGEngine:
    def __init__(self, config: dict[str, Any], log_dir: Path) -> None:
        self._config = config
        self._logger = setup_logger(__name__, log_dir)
        self._enabled = bool(config["rag"]["enabled"])
        self._collection = None
        self._client = None

        if not self._enabled:
            return

        if chromadb is None:
            self._logger.warning(
                "chromadb unavailable; RAG disabled. Install with: pip install chromadb"
            )
            self._enabled = False
            return

        index_dir = Path(config["paths"]["rag_index"])
        index_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(index_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=config["rag"]["collection_name"]
        )

    @property
    def enabled(self) -> bool:
        return self._enabled and self._collection is not None

    def ingest_code_index(self, code_index: dict[str, str]) -> int:
        if not self.enabled:
            return 0

        chunk_size = int(self._config["rag"]["chunk_size"])
        overlap = int(self._config["rag"]["chunk_overlap"])
        documents: list[str] = []
        metadatas: list[dict[str, str]] = []
        ids: list[str] = []

        for filepath, content in code_index.items():
            for chunk_index, chunk in enumerate(_chunk_text(content, chunk_size, overlap)):
                doc_id = _stable_id(filepath, chunk_index)
                documents.append(chunk)
                metadatas.append({"source": filepath, "type": "code"})
                ids.append(doc_id)

        if not documents:
            return 0

        self._collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        self._logger.info("Indexed %d code chunks into RAG", len(documents))
        return len(documents)

    def ingest_pdfs(self) -> int:
        if not self.enabled:
            return 0
        if PdfReader is None:
            self._logger.warning(
                "pypdf unavailable; PDF ingestion skipped. Install with: pip install pypdf"
            )
            return 0

        guild_dir = Path(self._config["paths"]["coders_guild"])
        if not guild_dir.exists():
            self._logger.info("CodersGuild path not found: %s", guild_dir)
            return 0

        chunk_size = int(self._config["rag"]["chunk_size"])
        overlap = int(self._config["rag"]["chunk_overlap"])
        documents: list[str] = []
        metadatas: list[dict[str, str]] = []
        ids: list[str] = []

        for pdf_path in guild_dir.rglob("*.pdf"):
            try:
                reader = PdfReader(str(pdf_path))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as exc:
                self._logger.warning("Failed to read %s: %s", pdf_path, exc)
                continue

            for chunk_index, chunk in enumerate(_chunk_text(text, chunk_size, overlap)):
                if not chunk.strip():
                    continue
                doc_id = _stable_id(str(pdf_path), chunk_index)
                documents.append(chunk)
                metadatas.append({"source": str(pdf_path), "type": "pdf"})
                ids.append(doc_id)

        if not documents:
            return 0

        self._collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        self._logger.info("Indexed %d PDF chunks into RAG", len(documents))
        return len(documents)

    def query(self, prompt: str) -> str:
        if not self.enabled:
            return ""

        top_k = int(self._config["rag"]["top_k"])
        results = self._collection.query(query_texts=[prompt], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        if not docs:
            return ""

        sections: list[str] = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source", "unknown")
            sections.append(f"[{meta.get('type', 'doc')}] {source}\n{doc}")
        return "\n\n---\n\n".join(sections)


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _stable_id(source: str, chunk_index: int) -> str:
    digest = hashlib.sha256(f"{source}:{chunk_index}".encode("utf-8")).hexdigest()
    return digest[:32]
