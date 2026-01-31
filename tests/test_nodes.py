"""Tests for node CRUD operations (Phase 2)."""

import pytest
from grafito import GrafitoDatabase, Node, NodeNotFoundError, InvalidPropertyError


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return GrafitoDatabase(':memory:')


def test_create_node_minimal(db):
    """Test creating a node with no labels or properties."""
    node = db.create_node()

    assert node.id == 1
    assert node.labels == []
    assert node.properties == {}


def test_create_node_with_labels(db):
    """Test creating a node with multiple labels."""
    node = db.create_node(labels=['Person', 'Employee'])

    assert node.id == 1
    assert set(node.labels) == {'Person', 'Employee'}
    assert node.properties == {}


def test_create_node_with_properties(db):
    """Test creating a node with properties."""
    properties = {
        'name': 'Alice',
        'age': 30,
        'score': 95.5,
        'active': True,
    }
    node = db.create_node(properties=properties)

    assert node.id == 1
    assert node.labels == []
    assert node.properties == properties


def test_create_node_with_labels_and_properties(db):
    """Test creating a complete node."""
    labels = ['Person', 'Employee', 'Developer']
    properties = {'name': 'Bob', 'age': 25, 'level': 'Senior'}

    node = db.create_node(labels=labels, properties=properties)

    assert node.id == 1
    assert set(node.labels) == set(labels)
    assert node.properties == properties


def test_create_multiple_nodes(db):
    """Test creating multiple nodes with incrementing IDs."""
    node1 = db.create_node(labels=['Person'], properties={'name': 'Alice'})
    node2 = db.create_node(labels=['Person'], properties={'name': 'Bob'})
    node3 = db.create_node(labels=['Company'], properties={'name': 'TechCorp'})

    assert node1.id == 1
    assert node2.id == 2
    assert node3.id == 3


def test_merge_node_creates_new(db):
    """Test merge_node creates a new node when no match exists."""
    node, created = db.merge_node(
        labels=['Person'],
        match_properties={'email': 'user@example.com'},
        on_create={'name': 'Alice'},
    )

    assert created is True
    assert set(node.labels) == {'Person'}
    assert node.properties == {'email': 'user@example.com', 'name': 'Alice'}


def test_merge_node_matches_existing(db):
    """Test merge_node returns existing node and applies on_match."""
    existing = db.create_node(
        labels=['Person'],
        properties={'email': 'user@example.com', 'name': 'Alice'}
    )

    node, created = db.merge_node(
        labels=['Person'],
        match_properties={'email': 'user@example.com'},
        on_create={'created_at': '2024-01-01'},
        on_match={'last_seen': '2024-02-01'},
    )

    assert created is False
    assert node.id == existing.id
    assert node.properties['email'] == 'user@example.com'
    assert node.properties['name'] == 'Alice'
    assert node.properties['last_seen'] == '2024-02-01'
    assert 'created_at' not in node.properties


def test_merge_node_label_mismatch_creates_new(db):
    """Test merge_node creates a new node when labels don't match."""
    existing = db.create_node(
        labels=['Company'],
        properties={'email': 'user@example.com', 'name': 'Acme'}
    )

    node, created = db.merge_node(
        labels=['Person'],
        match_properties={'email': 'user@example.com'},
        on_create={'name': 'Alice'},
    )

    assert created is True
    assert node.id != existing.id
    assert set(node.labels) == {'Person'}


def test_merge_node_empty_match_properties(db):
    """Test merge_node with empty match_properties."""
    node, created = db.merge_node(labels=['Person'])

    assert created is True
    assert set(node.labels) == {'Person'}


def test_create_node_with_invalid_property_type(db):
    """Test that invalid property types raise an error."""
    with pytest.raises(InvalidPropertyError) as exc_info:
        db.create_node(properties={'tags': {'python', 'sqlite'}})

    assert 'tags' in str(exc_info.value)


def test_get_node(db):
    """Test retrieving a node by ID."""
    created = db.create_node(
        labels=['Person', 'Employee'],
        properties={'name': 'Alice', 'age': 30}
    )

    retrieved = db.get_node(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert set(retrieved.labels) == set(created.labels)
    assert retrieved.properties == created.properties


def test_get_nonexistent_node(db):
    """Test that getting a non-existent node returns None."""
    node = db.get_node(999)
    assert node is None


def test_get_node_preserves_label_order(db):
    """Test that labels are returned in sorted order."""
    created = db.create_node(labels=['Zebra', 'Alpha', 'Beta'])

    retrieved = db.get_node(created.id)

    assert retrieved.labels == ['Alpha', 'Beta', 'Zebra']


def test_update_node_properties(db):
    """Test updating node properties."""
    node = db.create_node(properties={'name': 'Alice', 'age': 30})

    # Update age and add city
    success = db.update_node_properties(node.id, {'age': 31, 'city': 'NYC'})

    assert success is True

    updated = db.get_node(node.id)
    assert updated.properties == {'name': 'Alice', 'age': 31, 'city': 'NYC'}


def test_update_node_properties_overwrites_existing(db):
    """Test that updates overwrite existing values."""
    node = db.create_node(properties={'name': 'Alice', 'age': 30, 'city': 'LA'})

    db.update_node_properties(node.id, {'city': 'NYC'})

    updated = db.get_node(node.id)
    assert updated.properties['city'] == 'NYC'
    assert updated.properties['name'] == 'Alice'  # Other properties preserved


def test_update_nonexistent_node_properties(db):
    """Test that updating a non-existent node raises an error."""
    with pytest.raises(NodeNotFoundError) as exc_info:
        db.update_node_properties(999, {'name': 'Alice'})

    assert exc_info.value.node_id == 999


def test_add_labels_to_node(db):
    """Test adding labels to an existing node."""
    node = db.create_node(labels=['Person'])

    db.add_labels(node.id, ['Employee', 'Developer'])

    updated = db.get_node(node.id)
    assert set(updated.labels) == {'Person', 'Employee', 'Developer'}


def test_add_duplicate_label(db):
    """Test that adding a duplicate label is idempotent."""
    node = db.create_node(labels=['Person'])

    db.add_labels(node.id, ['Person', 'Employee'])

    updated = db.get_node(node.id)
    assert set(updated.labels) == {'Person', 'Employee'}


def test_add_labels_to_nonexistent_node(db):
    """Test that adding labels to non-existent node raises error."""
    with pytest.raises(NodeNotFoundError):
        db.add_labels(999, ['Person'])


def test_remove_labels_from_node(db):
    """Test removing labels from a node."""
    node = db.create_node(labels=['Person', 'Employee', 'Developer'])

    db.remove_labels(node.id, ['Employee', 'Developer'])

    updated = db.get_node(node.id)
    assert updated.labels == ['Person']


def test_remove_nonexistent_label(db):
    """Test that removing a non-existent label is safe."""
    node = db.create_node(labels=['Person'])

    db.remove_labels(node.id, ['NonExistent'])

    updated = db.get_node(node.id)
    assert updated.labels == ['Person']


def test_remove_labels_from_nonexistent_node(db):
    """Test that removing labels from non-existent node raises error."""
    with pytest.raises(NodeNotFoundError):
        db.remove_labels(999, ['Person'])


def test_delete_node(db):
    """Test deleting a node."""
    node = db.create_node(labels=['Person'], properties={'name': 'Alice'})

    success = db.delete_node(node.id)

    assert success is True

    # Verify node is gone
    deleted = db.get_node(node.id)
    assert deleted is None


def test_delete_nonexistent_node(db):
    """Test that deleting a non-existent node returns False."""
    success = db.delete_node(999)
    assert success is False


def test_delete_node_removes_labels(db):
    """Test that deleting a node also removes its labels from junction table."""
    node = db.create_node(labels=['Person', 'Employee'])

    db.delete_node(node.id)

    # Check that no labels remain in junction table
    cursor = db.conn.execute(
        "SELECT COUNT(*) FROM node_labels WHERE node_id = ?", (node.id,)
    )
    count = cursor.fetchone()[0]
    assert count == 0


def test_node_with_null_property(db):
    """Test that None/null properties are handled correctly."""
    node = db.create_node(properties={'name': 'Alice', 'middle_name': None})

    retrieved = db.get_node(node.id)
    assert retrieved.properties['middle_name'] is None


def test_transaction_rollback_on_error(db):
    """Test that failed operations rollback properly."""
    node = db.create_node(properties={'name': 'Alice'})

    try:
        # This should fail due to invalid property type
        db.update_node_properties(node.id, {'tags': {'invalid'}})
    except InvalidPropertyError:
        pass

    # Node should still have original properties
    retrieved = db.get_node(node.id)
    assert retrieved.properties == {'name': 'Alice'}


def test_context_manager_with_nodes(db):
    """Test that context manager commits node operations."""
    with db:
        node1 = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        node2 = db.create_node(labels=['Person'], properties={'name': 'Bob'})

    # Verify both nodes exist after context
    assert db.get_node(node1.id) is not None
    assert db.get_node(node2.id) is not None


def test_context_manager_rollback_on_exception(db):
    """Test that context manager rollback works on exception."""
    node = db.create_node(labels=['Person'], properties={'name': 'Alice'})

    try:
        with db:
            db.update_node_properties(node.id, {'name': 'Bob'})
            # Force an error
            raise ValueError("Test error")
    except ValueError:
        pass

    # Properties should not be updated due to rollback
    retrieved = db.get_node(node.id)
    assert retrieved.properties['name'] == 'Alice'
