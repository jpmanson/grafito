"""Custom exceptions for Grafito graph database."""


class GrafitoError(Exception):
    """Base exception for all Grafito errors."""
    pass


class NodeNotFoundError(GrafitoError):
    """Raised when a node with the given ID does not exist."""

    def __init__(self, node_id: int):
        self.node_id = node_id
        super().__init__(f"Node with ID {node_id} not found")


class RelationshipNotFoundError(GrafitoError):
    """Raised when a relationship with the given ID does not exist."""

    def __init__(self, relationship_id: int):
        self.relationship_id = relationship_id
        super().__init__(f"Relationship with ID {relationship_id} not found")


class InvalidLabelError(GrafitoError):
    """Raised when an invalid label name is provided."""

    def __init__(self, label: str, reason: str):
        self.label = label
        self.reason = reason
        super().__init__(f"Invalid label '{label}': {reason}")


class InvalidPropertyError(GrafitoError):
    """Raised when an invalid property type or value is provided."""

    def __init__(self, message: str):
        super().__init__(message)


class DatabaseError(GrafitoError):
    """Raised when a database operation fails."""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)


class ConstraintError(GrafitoError):
    """Raised when a schema constraint is violated."""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidFilterError(GrafitoError):
    """Raised when an invalid filter specification is provided."""

    def __init__(self, message: str):
        super().__init__(message)
