"""LEANN indexer configuration."""

from __future__ import annotations

from .base import Indexer


class LEANNIndexer(Indexer):
    backend = "leann"
