import math

import pytest

from grafito.cypher import format_vector_literal


def test_format_vector_literal_basic():
    literal = format_vector_literal([1.2, -3.4], precision=3)
    assert literal == "[1.200,-3.400]"


def test_format_vector_literal_rejects_nan():
    with pytest.raises(ValueError, match="finite"):
        format_vector_literal([math.nan])


def test_format_vector_literal_rejects_non_numeric():
    with pytest.raises(ValueError, match="numeric"):
        format_vector_literal(["bad"])
