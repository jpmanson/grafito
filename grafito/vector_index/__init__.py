"""Vector index backends for Grafito."""

from .base import VectorIndex
from .bruteforce import BruteForceIndex

FaissIndex = None  # type: ignore[assignment]
AnnoyIndexBackend = None  # type: ignore[assignment]
LeannIndexBackend = None  # type: ignore[assignment]
HNSWlibIndexBackend = None  # type: ignore[assignment]
USearchIndexBackend = None  # type: ignore[assignment]
VoyagerIndexBackend = None  # type: ignore[assignment]

__all__ = [
    "VectorIndex",
    "BruteForceIndex",
    "AnnoyIndexBackend",
    "LeannIndexBackend",
    "HNSWlibIndexBackend",
    "FaissIndex",
    "USearchIndexBackend",
    "VoyagerIndexBackend",
]


def __getattr__(name: str):
    if name == "FaissIndex":
        from .faiss import FaissIndex as _FaissIndex

        return _FaissIndex
    if name == "AnnoyIndexBackend":
        from .annoy import AnnoyIndexBackend as _AnnoyIndexBackend

        return _AnnoyIndexBackend
    if name == "LeannIndexBackend":
        from .leann import LeannIndexBackend as _LeannIndexBackend

        return _LeannIndexBackend
    if name == "HNSWlibIndexBackend":
        from .hnswlib import HNSWlibIndexBackend as _HNSWlibIndexBackend

        return _HNSWlibIndexBackend
    if name == "USearchIndexBackend":
        from .usearch import USearchIndexBackend as _USearchIndexBackend

        return _USearchIndexBackend
    if name == "VoyagerIndexBackend":
        from .voyager import VoyagerIndexBackend as _VoyagerIndexBackend

        return _VoyagerIndexBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name}")
