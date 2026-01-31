"""Text index backends for full-text search."""

from .base import TextIndex
from .sqlite_fts import SQLiteFTSIndex

__all__ = [
    "TextIndex",
    "SQLiteFTSIndex",
]

# Optional: BM25S backend (requires bm25s package)
try:
    from .bm25s import BM25SIndex
    __all__.append("BM25SIndex")
except ImportError:
    pass

