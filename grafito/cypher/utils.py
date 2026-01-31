"""Cypher helper utilities."""

from __future__ import annotations

import math
from typing import Iterable


def format_vector_literal(vector: Iterable[float], precision: int = 8) -> str:
    """Format a numeric vector literal for Cypher.

    Args:
        vector: Iterable of numeric values.
        precision: Fixed decimal precision to avoid scientific notation.

    Returns:
        Cypher list literal string, e.g. "[0.10000000,-1.25000000]".

    Raises:
        ValueError: If vector values are non-numeric or non-finite.
    """
    if not isinstance(precision, int) or precision < 0:
        raise ValueError("precision must be a non-negative integer")

    values = []
    for value in vector:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Vector values must be numeric") from exc
        if not math.isfinite(number):
            raise ValueError("Vector values must be finite")
        values.append(number)

    fmt = f"{{:.{precision}f}}"
    return "[" + ",".join(fmt.format(value) for value in values) + "]"
