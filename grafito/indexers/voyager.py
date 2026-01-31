"""Voyager indexer configuration."""

from __future__ import annotations

from .base import Indexer


class VoyagerIndexer(Indexer):
    backend = "voyager"
