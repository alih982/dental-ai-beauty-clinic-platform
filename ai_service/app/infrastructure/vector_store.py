"""Stub vector store - avoids pgvector dependency for initial deployment"""
import logging

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Stub DocumentChunk class."""
    pass


def init_db():
    """No-op for stub implementation."""
    logger.info("Vector store initialization skipped (stub mode)")
