"""Database schema definition and initialization for Grafito."""

import sqlite3

# SQL schema for the Property Graph Model
SCHEMA_SQL = """
-- Nodes: core entities of the graph
CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL DEFAULT (julianday('now')),
    properties TEXT DEFAULT '{}',
    uri TEXT
);

-- Labels: normalized label names
CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- Junction table: many-to-many relationship between nodes and labels
CREATE TABLE IF NOT EXISTS node_labels (
    node_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    PRIMARY KEY (node_id, label_id),
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);

-- Relationships: directed connections between nodes
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id INTEGER NOT NULL,
    target_node_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    created_at REAL NOT NULL DEFAULT (julianday('now')),
    properties TEXT DEFAULT '{}',
    uri TEXT,
    FOREIGN KEY (source_node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Property index registry (metadata for custom indexes)
CREATE TABLE IF NOT EXISTS property_indexes (
    name TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    label_or_type TEXT,
    property TEXT NOT NULL,
    unique_flag INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL DEFAULT (julianday('now'))
);

-- Property constraints registry (metadata for schema constraints)
CREATE TABLE IF NOT EXISTS property_constraints (
    name TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    label_or_type TEXT NOT NULL,
    property TEXT NOT NULL,
    constraint_type TEXT NOT NULL,
    type_name TEXT,
    created_at REAL NOT NULL DEFAULT (julianday('now'))
);

-- Vector index registry (metadata)
CREATE TABLE IF NOT EXISTS vector_indexes (
    name TEXT PRIMARY KEY,
    dim INTEGER NOT NULL,
    backend TEXT NOT NULL,
    method TEXT NOT NULL,
    options TEXT,
    created_at REAL NOT NULL DEFAULT (julianday('now'))
);

-- Vector entries (optional persistence)
CREATE TABLE IF NOT EXISTS vector_entries (
    index_name TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    vector TEXT NOT NULL,
    updated_at REAL NOT NULL DEFAULT (julianday('now')),
    PRIMARY KEY (index_name, node_id)
);

-- Full-text search (FTS5) index
CREATE VIRTUAL TABLE IF NOT EXISTS fts_index USING fts5(
    entity_type,
    entity_id UNINDEXED,
    label_type,
    content,
    tokenize = 'unicode61'
);

-- Full-text search configuration
CREATE TABLE IF NOT EXISTS fts_config (
    entity_type TEXT NOT NULL,
    label_type TEXT,
    property TEXT NOT NULL,
    weight REAL
);

-- Full-text search triggers (materialized index)
CREATE TRIGGER IF NOT EXISTS node_fts_insert
AFTER INSERT ON nodes
BEGIN
    INSERT INTO fts_index (entity_type, entity_id, label_type, content)
    SELECT
        'node',
        NEW.id,
        l.name,
        (
            SELECT group_concat(
                       CAST(json_extract(NEW.properties, '$.' || c.property) AS TEXT),
                       ' '
                   )
            FROM fts_config c
            WHERE c.entity_type = 'node'
              AND (c.label_type IS NULL OR c.label_type = l.name)
              AND json_extract(NEW.properties, '$.' || c.property) IS NOT NULL
        )
    FROM labels l
    JOIN node_labels nl ON nl.label_id = l.id
    WHERE nl.node_id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS node_fts_update
AFTER UPDATE ON nodes
BEGIN
    DELETE FROM fts_index
    WHERE entity_type = 'node' AND entity_id = NEW.id;

    INSERT INTO fts_index (entity_type, entity_id, label_type, content)
    SELECT
        'node',
        NEW.id,
        l.name,
        (
            SELECT group_concat(
                       CAST(json_extract(NEW.properties, '$.' || c.property) AS TEXT),
                       ' '
                   )
            FROM fts_config c
            WHERE c.entity_type = 'node'
              AND (c.label_type IS NULL OR c.label_type = l.name)
              AND json_extract(NEW.properties, '$.' || c.property) IS NOT NULL
        )
    FROM labels l
    JOIN node_labels nl ON nl.label_id = l.id
    WHERE nl.node_id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS node_fts_delete
AFTER DELETE ON nodes
BEGIN
    DELETE FROM fts_index
    WHERE entity_type = 'node' AND entity_id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS node_label_insert
AFTER INSERT ON node_labels
BEGIN
    DELETE FROM fts_index
    WHERE entity_type = 'node' AND entity_id = NEW.node_id;

    INSERT INTO fts_index (entity_type, entity_id, label_type, content)
    SELECT
        'node',
        n.id,
        l.name,
        (
            SELECT group_concat(
                       CAST(json_extract(n.properties, '$.' || c.property) AS TEXT),
                       ' '
                   )
            FROM fts_config c
            WHERE c.entity_type = 'node'
              AND (c.label_type IS NULL OR c.label_type = l.name)
              AND json_extract(n.properties, '$.' || c.property) IS NOT NULL
        )
    FROM nodes n
    JOIN node_labels nl ON nl.node_id = n.id
    JOIN labels l ON l.id = nl.label_id
    WHERE n.id = NEW.node_id;
END;

CREATE TRIGGER IF NOT EXISTS node_label_delete
AFTER DELETE ON node_labels
BEGIN
    DELETE FROM fts_index
    WHERE entity_type = 'node' AND entity_id = OLD.node_id;

    INSERT INTO fts_index (entity_type, entity_id, label_type, content)
    SELECT
        'node',
        n.id,
        l.name,
        (
            SELECT group_concat(
                       CAST(json_extract(n.properties, '$.' || c.property) AS TEXT),
                       ' '
                   )
            FROM fts_config c
            WHERE c.entity_type = 'node'
              AND (c.label_type IS NULL OR c.label_type = l.name)
              AND json_extract(n.properties, '$.' || c.property) IS NOT NULL
        )
    FROM nodes n
    JOIN node_labels nl ON nl.node_id = n.id
    JOIN labels l ON l.id = nl.label_id
    WHERE n.id = OLD.node_id;
END;

CREATE TRIGGER IF NOT EXISTS rel_fts_insert
AFTER INSERT ON relationships
BEGIN
    INSERT INTO fts_index (entity_type, entity_id, label_type, content)
    SELECT
        'relationship',
        NEW.id,
        NEW.type,
        (
            SELECT group_concat(
                       CAST(json_extract(NEW.properties, '$.' || c.property) AS TEXT),
                       ' '
                   )
            FROM fts_config c
            WHERE c.entity_type = 'relationship'
              AND (c.label_type IS NULL OR c.label_type = NEW.type)
              AND json_extract(NEW.properties, '$.' || c.property) IS NOT NULL
        );
END;

CREATE TRIGGER IF NOT EXISTS rel_fts_update
AFTER UPDATE ON relationships
BEGIN
    DELETE FROM fts_index
    WHERE entity_type = 'relationship' AND entity_id = NEW.id;

    INSERT INTO fts_index (entity_type, entity_id, label_type, content)
    SELECT
        'relationship',
        NEW.id,
        NEW.type,
        (
            SELECT group_concat(
                       CAST(json_extract(NEW.properties, '$.' || c.property) AS TEXT),
                       ' '
                   )
            FROM fts_config c
            WHERE c.entity_type = 'relationship'
              AND (c.label_type IS NULL OR c.label_type = NEW.type)
              AND json_extract(NEW.properties, '$.' || c.property) IS NOT NULL
        );
END;

CREATE TRIGGER IF NOT EXISTS rel_fts_delete
AFTER DELETE ON relationships
BEGIN
    DELETE FROM fts_index
    WHERE entity_type = 'relationship' AND entity_id = OLD.id;
END;
"""

# Indices for query performance
INDICES_SQL = """
-- Index for label lookups
CREATE INDEX IF NOT EXISTS idx_node_labels_label ON node_labels(label_id);

-- Indices for relationship traversal
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_node_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_node_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type);

-- Index for label name lookups
CREATE INDEX IF NOT EXISTS idx_labels_name ON labels(name);

-- Index for property index registry
CREATE INDEX IF NOT EXISTS idx_property_indexes_entity ON property_indexes(entity);

-- Index for constraint registry
CREATE INDEX IF NOT EXISTS idx_property_constraints_entity ON property_constraints(entity);

-- Index for FTS config lookup
CREATE INDEX IF NOT EXISTS idx_fts_config_entity ON fts_config(entity_type);
CREATE INDEX IF NOT EXISTS idx_fts_config_label ON fts_config(entity_type, label_type);
"""


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Initialize the database schema.

    Args:
        conn: SQLite database connection

    This function creates all necessary tables and indices for the Property Graph Model.
    It's safe to call multiple times (uses IF NOT EXISTS).
    """
    # Enable foreign key constraints (required for CASCADE deletes)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create tables
    try:
        conn.executescript(SCHEMA_SQL)
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "fts5" in message and "no such module" in message:
            raise sqlite3.OperationalError(
                "SQLite FTS5 is required for text search. "
                "Use an SQLite build with FTS5 enabled."
            ) from exc
        raise

    _ensure_column(conn, "nodes", "uri", "uri TEXT")
    _ensure_column(conn, "relationships", "uri", "uri TEXT")

    # Create indices
    conn.executescript(INDICES_SQL)

    # Commit changes
    conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    """Add a column to an existing table if it is missing."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def drop_schema(conn: sqlite3.Connection) -> None:
    """Drop all tables and indices (useful for testing).

    Args:
        conn: SQLite database connection

    Warning: This will delete all data in the database.
    """
    conn.executescript("""
        DROP TABLE IF EXISTS relationships;
        DROP TABLE IF EXISTS property_indexes;
        DROP TABLE IF EXISTS property_constraints;
        DROP TABLE IF EXISTS vector_indexes;
        DROP TABLE IF EXISTS vector_entries;
        DROP TABLE IF EXISTS fts_index;
        DROP TABLE IF EXISTS fts_config;
        DROP TRIGGER IF EXISTS node_fts_insert;
        DROP TRIGGER IF EXISTS node_fts_update;
        DROP TRIGGER IF EXISTS node_fts_delete;
        DROP TRIGGER IF EXISTS node_label_insert;
        DROP TRIGGER IF EXISTS node_label_delete;
        DROP TRIGGER IF EXISTS rel_fts_insert;
        DROP TRIGGER IF EXISTS rel_fts_update;
        DROP TRIGGER IF EXISTS rel_fts_delete;
        DROP TABLE IF EXISTS node_labels;
        DROP TABLE IF EXISTS labels;
        DROP TABLE IF EXISTS nodes;
        DROP INDEX IF EXISTS idx_node_labels_label;
        DROP INDEX IF EXISTS idx_relationships_source;
        DROP INDEX IF EXISTS idx_relationships_target;
        DROP INDEX IF EXISTS idx_relationships_type;
        DROP INDEX IF EXISTS idx_labels_name;
        DROP INDEX IF EXISTS idx_property_indexes_entity;
        DROP INDEX IF EXISTS idx_property_constraints_entity;
        DROP INDEX IF EXISTS idx_fts_config_entity;
        DROP INDEX IF EXISTS idx_fts_config_label;
    """)
    conn.commit()
