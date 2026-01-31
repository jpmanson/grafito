"""Cypher query language support for Grafito.

This module provides a Cypher query parser and executor that translates
Cypher queries to Grafito's programmatic API.

Supported subset:
- CREATE (n:Label {props})
- MATCH (n:Label) WHERE condition RETURN projection
- Relationship patterns: (a)-[r:TYPE]->(b)
- WHERE expressions: =, !=, <, >, <=, >=, AND, OR, NOT
"""

from .exceptions import CypherSyntaxError, CypherExecutionError
from .utils import format_vector_literal

__all__ = ['CypherSyntaxError', 'CypherExecutionError', 'format_vector_literal']
