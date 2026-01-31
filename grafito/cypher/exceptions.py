"""Exceptions for Cypher query processing."""


class CypherError(Exception):
    """Base exception for Cypher-related errors."""
    pass


class CypherSyntaxError(CypherError):
    """Raised when a Cypher query has invalid syntax."""

    def __init__(self, message: str, line: int = 1, column: int = 1):
        self.line = line
        self.column = column
        super().__init__(f"Syntax error at line {line}, column {column}: {message}")


class CypherExecutionError(CypherError):
    """Raised when a Cypher query fails during execution."""
    pass
