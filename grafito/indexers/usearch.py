"""USearch indexer configuration."""

from __future__ import annotations

from .base import Indexer


class USearchIndexer(Indexer):
    backend = "usearch"
