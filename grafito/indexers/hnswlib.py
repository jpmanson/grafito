"""HNSWlib indexer configuration."""

from __future__ import annotations

from .base import Indexer


class HNSWlibIndexer(Indexer):
    backend = "hnswlib"
