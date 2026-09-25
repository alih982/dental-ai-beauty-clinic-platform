"""Stub RAG service - avoids pgvector dependency for initial deployment"""
import logging
from typing import AsyncGenerator, Dict, Any

logger = logging.getLogger(__name__)


class RagService:
    """Minimal RAG stub for initial deployment without PostgreSQL/pgvector."""

    async def ingest_document(
        self, db, file_path: str, metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Stub - returns placeholder result."""
        logger.warning("RAG ingest not configured - returning placeholder")
        return {"chunks_processed": 0}

    async def query(
        self, db, question: str
    ) -> Dict[str, Any]:
        """Stub - returns placeholder result."""
        logger.warning("RAG query not configured - returning placeholder")
        return {
            "answer": "سیستم جستجوی هوشمند هنوز راه‌اندازی نشده است.",
            "sources": []
        }

    async def query_stream(
        self, db, question: str
    ) -> AsyncGenerator[str, None]:
        """Return a simple message when RAG is not available."""
        logger.warning("RAG not configured - using placeholder response")
        msg = "سیستم جستجوی هوشمند هنوز راه‌اندازی نشده است. لطفاً بعداً امتحان کنید."
        for word in msg.split():
            yield word + " "


rag_service = RagService()
