"""Annoy indexer configuration."""

from __future__ import annotations

from .base import Indexer


class AnnoyIndexer(Indexer):
    backend = "annoy"
