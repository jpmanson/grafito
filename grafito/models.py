"""Data models for Grafito graph database entities."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """Represents a node in the property graph.

    Attributes:
        id: Unique identifier assigned by the database
        labels: List of labels classifying this node (e.g., ['Person', 'Employee'])
        properties: Dictionary of properties as key-value pairs
        uri: Optional URI for RDF export or external identity
    """

    id: int
    labels: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    uri: str | None = None

    def to_dict(self) -> dict:
        """Convert node to dictionary representation.

        Returns:
            Dictionary with id, labels, and properties
        """
        return {
            'id': self.id,
            'labels': self.labels.copy(),
            'properties': self.properties.copy(),
            'uri': self.uri,
        }

    def __repr__(self) -> str:
        """Human-readable representation in Cypher-like format.

        Returns:
            String like "(1:Person:Employee {name: 'Alice', age: 30})"
        """
        labels_str = ':'.join(self.labels) if self.labels else ''
        if labels_str:
            labels_str = ':' + labels_str

        props_items = ', '.join(f"{k}: {repr(v)}" for k, v in self.properties.items())
        props_str = f" {{{props_items}}}" if props_items else ''

        return f"({self.id}{labels_str}{props_str})"


@dataclass
class Relationship:
    """Represents a directed relationship between two nodes.

    Attributes:
        id: Unique identifier assigned by the database
        source_id: ID of the source (origin) node
        target_id: ID of the target (destination) node
        type: Relationship type (e.g., 'WORKS_AT', 'KNOWS')
        properties: Dictionary of properties as key-value pairs
        uri: Optional URI for RDF export or external identity
    """

    id: int
    source_id: int
    target_id: int
    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    uri: str | None = None

    def to_dict(self) -> dict:
        """Convert relationship to dictionary representation.

        Returns:
            Dictionary with id, source_id, target_id, type, and properties
        """
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type,
            'properties': self.properties.copy(),
            'uri': self.uri,
        }

    def __repr__(self) -> str:
        """Human-readable representation in Cypher-like format.

        Returns:
            String like "({source_id})-[{type} {properties}]->({target_id})"
        """
        props_items = ', '.join(f"{k}: {repr(v)}" for k, v in self.properties.items())
        props_str = f" {{{props_items}}}" if props_items else ''

        return f"({self.source_id})-[{self.type}{props_str}]->({self.target_id})"


@dataclass
class Path:
    """Represents a path as ordered nodes and relationships."""

    nodes: list[Node] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert path to dictionary representation."""
        return {
            'nodes': [node.to_dict() for node in self.nodes],
            'relationships': [rel.to_dict() for rel in self.relationships],
        }


@dataclass
class Point:
    """Represents a spatial point (cartesian or WGS84)."""

    x: float | None = None
    y: float | None = None
    z: float | None = None
    longitude: float | None = None
    latitude: float | None = None
    height: float | None = None
    srid: int | None = None

    def to_dict(self) -> dict:
        """Convert point to dictionary representation."""
        data = {}
        if self.x is not None:
            data['x'] = self.x
        if self.y is not None:
            data['y'] = self.y
        if self.z is not None:
            data['z'] = self.z
        if self.longitude is not None:
            data['longitude'] = self.longitude
        if self.latitude is not None:
            data['latitude'] = self.latitude
        if self.height is not None:
            data['height'] = self.height
        if self.srid is not None:
            data['srid'] = self.srid
        return data
