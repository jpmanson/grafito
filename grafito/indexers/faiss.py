"""FAISS indexer configuration."""

from __future__ import annotations

from .base import Indexer


class FAISSIndexer(Indexer):
    backend = "faiss"
