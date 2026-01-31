"""Tests for multi-label functionality (Phase 2)."""

import pytest
from grafito import GrafitoDatabase, Node


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return GrafitoDatabase(':memory:')


def test_node_with_no_labels(db):
    """Test that nodes can exist without labels."""
    node = db.create_node(properties={'name': 'Alice'})

    assert node.labels == []

    retrieved = db.get_node(node.id)
    assert retrieved.labels == []


def test_node_with_single_label(db):
    """Test node with one label."""
    node = db.create_node(labels=['Person'])

    assert node.labels == ['Person']

    retrieved = db.get_node(node.id)
    assert retrieved.labels == ['Person']


def test_node_with_multiple_labels(db):
    """Test node with multiple labels."""
    node = db.create_node(labels=['Person', 'Employee', 'Developer'])

    assert set(node.labels) == {'Person', 'Employee', 'Developer'}

    retrieved = db.get_node(node.id)
    assert set(retrieved.labels) == {'Person', 'Employee', 'Developer'}


def test_labels_are_case_insensitive(db):
    """Test that labels are stored case-insensitively."""
    node1 = db.create_node(labels=['Person'])
    node2 = db.create_node(labels=['person'])  # lowercase

    # Both should create the same label
    cursor = db.conn.execute("SELECT COUNT(*) FROM labels")
    label_count = cursor.fetchone()[0]

    assert label_count == 1  # Only one label created


def test_labels_shared_across_nodes(db):
    """Test that labels are shared/normalized across nodes."""
    node1 = db.create_node(labels=['Person', 'Employee'])
    node2 = db.create_node(labels=['Person', 'Manager'])
    node3 = db.create_node(labels=['Employee', 'Developer'])

    # Check that only 4 unique labels exist
    cursor = db.conn.execute("SELECT COUNT(*) FROM labels")
    label_count = cursor.fetchone()[0]

    assert label_count == 4  # Person, Employee, Manager, Developer


def test_add_labels_incrementally(db):
    """Test adding labels one at a time."""
    node = db.create_node(labels=['Person'])

    db.add_labels(node.id, ['Employee'])
    assert set(db.get_node(node.id).labels) == {'Person', 'Employee'}

    db.add_labels(node.id, ['Developer'])
    assert set(db.get_node(node.id).labels) == {'Person', 'Employee', 'Developer'}

    db.add_labels(node.id, ['Manager'])
    assert set(db.get_node(node.id).labels) == {
        'Person',
        'Employee',
        'Developer',
        'Manager',
    }


def test_remove_labels_incrementally(db):
    """Test removing labels one at a time."""
    node = db.create_node(labels=['Person', 'Employee', 'Developer', 'Manager'])

    db.remove_labels(node.id, ['Manager'])
    assert set(db.get_node(node.id).labels) == {'Person', 'Employee', 'Developer'}

    db.remove_labels(node.id, ['Employee'])
    assert set(db.get_node(node.id).labels) == {'Person', 'Developer'}

    db.remove_labels(node.id, ['Developer'])
    assert db.get_node(node.id).labels == ['Person']


def test_remove_all_labels(db):
    """Test removing all labels from a node."""
    node = db.create_node(labels=['Person', 'Employee', 'Developer'])

    db.remove_labels(node.id, ['Person', 'Employee', 'Developer'])

    retrieved = db.get_node(node.id)
    assert retrieved.labels == []


def test_add_multiple_labels_at_once(db):
    """Test adding multiple labels in one call."""
    node = db.create_node(labels=['Person'])

    db.add_labels(node.id, ['Employee', 'Developer', 'Manager'])

    assert set(db.get_node(node.id).labels) == {
        'Person',
        'Employee',
        'Developer',
        'Manager',
    }


def test_remove_multiple_labels_at_once(db):
    """Test removing multiple labels in one call."""
    node = db.create_node(labels=['Person', 'Employee', 'Developer', 'Manager'])

    db.remove_labels(node.id, ['Employee', 'Developer'])

    assert set(db.get_node(node.id).labels) == {'Person', 'Manager'}


def test_label_names_with_special_characters(db):
    """Test that labels can have special characters."""
    labels = ['Person-Employee', 'Manager_V2', 'Level:Senior']

    node = db.create_node(labels=labels)

    retrieved = db.get_node(node.id)
    assert set(retrieved.labels) == set(labels)


def test_labels_sorted_alphabetically(db):
    """Test that labels are returned in sorted order."""
    node = db.create_node(labels=['Zebra', 'Alpha', 'Beta', 'Gamma'])

    retrieved = db.get_node(node.id)
    assert retrieved.labels == ['Alpha', 'Beta', 'Gamma', 'Zebra']


def test_different_nodes_different_labels(db):
    """Test that different nodes can have different labels."""
    person = db.create_node(labels=['Person'], properties={'name': 'Alice'})
    company = db.create_node(labels=['Company'], properties={'name': 'TechCorp'})
    product = db.create_node(labels=['Product'], properties={'name': 'Widget'})

    assert db.get_node(person.id).labels == ['Person']
    assert db.get_node(company.id).labels == ['Company']
    assert db.get_node(product.id).labels == ['Product']


def test_different_nodes_same_labels(db):
    """Test that multiple nodes can share the same labels."""
    alice = db.create_node(labels=['Person', 'Employee'], properties={'name': 'Alice'})
    bob = db.create_node(labels=['Person', 'Employee'], properties={'name': 'Bob'})
    charlie = db.create_node(
        labels=['Person', 'Employee'], properties={'name': 'Charlie'}
    )

    assert set(db.get_node(alice.id).labels) == {'Person', 'Employee'}
    assert set(db.get_node(bob.id).labels) == {'Person', 'Employee'}
    assert set(db.get_node(charlie.id).labels) == {'Person', 'Employee'}


def test_empty_labels_list(db):
    """Test that empty labels list works correctly."""
    node = db.create_node(labels=[])

    assert node.labels == []

    retrieved = db.get_node(node.id)
    assert retrieved.labels == []


def test_add_empty_labels_list(db):
    """Test that adding empty labels list is safe."""
    node = db.create_node(labels=['Person'])

    db.add_labels(node.id, [])

    assert db.get_node(node.id).labels == ['Person']


def test_remove_empty_labels_list(db):
    """Test that removing empty labels list is safe."""
    node = db.create_node(labels=['Person'])

    db.remove_labels(node.id, [])

    assert db.get_node(node.id).labels == ['Person']


def test_labels_persist_after_property_update(db):
    """Test that labels are not affected by property updates."""
    node = db.create_node(labels=['Person', 'Employee'], properties={'name': 'Alice'})

    db.update_node_properties(node.id, {'name': 'Alicia', 'age': 30})

    retrieved = db.get_node(node.id)
    assert set(retrieved.labels) == {'Person', 'Employee'}
    assert retrieved.properties['name'] == 'Alicia'


def test_label_reuse_after_node_deletion(db):
    """Test that labels can be reused after nodes are deleted."""
    node1 = db.create_node(labels=['Person'])

    cursor = db.conn.execute("SELECT COUNT(*) FROM labels")
    label_count_before = cursor.fetchone()[0]

    db.delete_node(node1.id)

    # Create new node with same label
    node2 = db.create_node(labels=['Person'])

    cursor = db.conn.execute("SELECT COUNT(*) FROM labels")
    label_count_after = cursor.fetchone()[0]

    # Label should be reused, not duplicated
    assert label_count_before == label_count_after
