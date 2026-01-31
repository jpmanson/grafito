"""Tests for database initialization and basic infrastructure (Phase 1)."""

import pytest
import sqlite3

from grafito import GrafitoDatabase, Node, Relationship, DatabaseError


def test_database_initialization():
    """Test that database initializes correctly."""
    db = GrafitoDatabase(':memory:')
    assert db.conn is not None
    assert isinstance(db.conn, sqlite3.Connection)


def test_schema_creation():
    """Test that all tables are created."""
    db = GrafitoDatabase(':memory:')

    # Check that tables exist
    cursor = db.conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    assert 'nodes' in tables
    assert 'labels' in tables
    assert 'node_labels' in tables
    assert 'relationships' in tables


def test_indices_creation():
    """Test that indices are created."""
    db = GrafitoDatabase(':memory:')

    cursor = db.conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='index' AND name LIKE 'idx_%'
        ORDER BY name
    """)
    indices = [row[0] for row in cursor.fetchall()]

    assert 'idx_node_labels_label' in indices
    assert 'idx_relationships_source' in indices
    assert 'idx_relationships_target' in indices
    assert 'idx_relationships_type' in indices
    assert 'idx_labels_name' in indices


def test_foreign_keys_enabled():
    """Test that foreign keys are enabled."""
    db = GrafitoDatabase(':memory:')

    cursor = db.conn.execute("PRAGMA foreign_keys")
    result = cursor.fetchone()[0]

    assert result == 1  # Foreign keys are ON


def test_context_manager():
    """Test that database works as context manager."""
    with GrafitoDatabase(':memory:') as db:
        assert db.conn is not None
        assert db._in_transaction is True

    # After exiting context, transaction should be committed
    assert db._in_transaction is False


def test_transaction_methods():
    """Test explicit transaction control."""
    db = GrafitoDatabase(':memory:')

    # Initially not in transaction
    assert db._in_transaction is False

    # Begin transaction
    db.begin_transaction()
    assert db._in_transaction is True

    # Commit
    db.commit()
    assert db._in_transaction is False

    # Begin and rollback
    db.begin_transaction()
    assert db._in_transaction is True
    db.rollback()
    assert db._in_transaction is False


def test_close_connection():
    """Test that connection can be closed."""
    db = GrafitoDatabase(':memory:')
    db.close()

    # After closing, operations should fail
    with pytest.raises(Exception):
        db.conn.execute("SELECT 1")


def test_validate_properties_valid():
    """Test property validation with valid types."""
    db = GrafitoDatabase(':memory:')

    properties = {
        'name': 'Alice',
        'age': 30,
        'score': 95.5,
        'active': True,
        'nullable': None,
    }

    result = db._validate_properties(properties)
    assert result == properties


def test_validate_properties_invalid():
    """Test property validation with invalid types."""
    from grafito import InvalidPropertyError

    db = GrafitoDatabase(':memory:')

    # Set is not supported
    properties = {'tags': {'python', 'database'}}
    with pytest.raises(InvalidPropertyError) as exc_info:
        db._validate_properties(properties)

    assert 'tags' in str(exc_info.value)
    assert 'set' in str(exc_info.value)


def test_validate_properties_temporal():
    """Test property validation with temporal types."""
    from datetime import date, datetime, time, timezone

    db = GrafitoDatabase(':memory:')

    properties = {
        'born': date(2024, 1, 2),
        'last_seen': datetime(2024, 1, 2, 10, 11, 12),
        'alarm': time(10, 11, 12),
        'last_seen_utc': datetime(2024, 1, 2, 10, 11, 12, tzinfo=timezone.utc),
        'alarm_utc': time(10, 11, 12, tzinfo=timezone.utc),
    }

    result = db._validate_properties(properties)
    assert result == {
        'born': '2024-01-02',
        'last_seen': '2024-01-02T10:11:12',
        'alarm': '10:11:12',
        'last_seen_utc': '2024-01-02T10:11:12Z',
        'alarm_utc': '10:11:12+00:00',
    }


def test_node_model():
    """Test Node dataclass."""
    node = Node(id=1, labels=['Person', 'Employee'], properties={'name': 'Alice', 'age': 30})

    assert node.id == 1
    assert node.labels == ['Person', 'Employee']
    assert node.properties == {'name': 'Alice', 'age': 30}

    # Test to_dict
    node_dict = node.to_dict()
    assert node_dict['id'] == 1
    assert node_dict['labels'] == ['Person', 'Employee']
    assert node_dict['properties'] == {'name': 'Alice', 'age': 30}

    # Test repr
    repr_str = repr(node)
    assert '1' in repr_str
    assert 'Person' in repr_str
    assert 'Employee' in repr_str
    assert 'Alice' in repr_str


def test_relationship_model():
    """Test Relationship dataclass."""
    rel = Relationship(
        id=1,
        source_id=10,
        target_id=20,
        type='WORKS_AT',
        properties={'since': 2020}
    )

    assert rel.id == 1
    assert rel.source_id == 10
    assert rel.target_id == 20
    assert rel.type == 'WORKS_AT'
    assert rel.properties == {'since': 2020}

    # Test to_dict
    rel_dict = rel.to_dict()
    assert rel_dict['id'] == 1
    assert rel_dict['source_id'] == 10
    assert rel_dict['target_id'] == 20
    assert rel_dict['type'] == 'WORKS_AT'

    # Test repr
    repr_str = repr(rel)
    assert '10' in repr_str
    assert '20' in repr_str
    assert 'WORKS_AT' in repr_str
