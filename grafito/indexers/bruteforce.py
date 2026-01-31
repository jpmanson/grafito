"""Brute-force indexer configuration."""

from __future__ import annotations

from .base import Indexer


class BruteForceIndexer(Indexer):
    backend = "bruteforce"
