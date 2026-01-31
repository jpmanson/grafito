"""Tests for relationship CRUD operations (Phase 3)."""

import pytest
from grafito import (
    GrafitoDatabase,
    Relationship,
    NodeNotFoundError,
    InvalidPropertyError,
)


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return GrafitoDatabase(':memory:')


@pytest.fixture
def sample_nodes(db):
    """Create sample nodes for testing relationships."""
    alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
    bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
    company = db.create_node(labels=['Company'], properties={'name': 'TechCorp'})
    return {'alice': alice, 'bob': bob, 'company': company}


def test_create_relationship_minimal(db, sample_nodes):
    """Test creating a relationship without properties."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel = db.create_relationship(alice.id, bob.id, 'KNOWS')

    assert rel.id == 1
    assert rel.source_id == alice.id
    assert rel.target_id == bob.id
    assert rel.type == 'KNOWS'
    assert rel.properties == {}


def test_create_relationship_with_properties(db, sample_nodes):
    """Test creating a relationship with properties."""
    alice = sample_nodes['alice']
    company = sample_nodes['company']

    properties = {'since': 2020, 'position': 'Engineer', 'active': True}
    rel = db.create_relationship(
        alice.id, company.id, 'WORKS_AT', properties=properties
    )

    assert rel.id == 1
    assert rel.source_id == alice.id
    assert rel.target_id == company.id
    assert rel.type == 'WORKS_AT'
    assert rel.properties == properties


def test_create_multiple_relationships(db, sample_nodes):
    """Test creating multiple relationships with incrementing IDs."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']
    company = sample_nodes['company']

    rel1 = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel2 = db.create_relationship(alice.id, company.id, 'WORKS_AT')
    rel3 = db.create_relationship(bob.id, company.id, 'WORKS_AT')

    assert rel1.id == 1
    assert rel2.id == 2
    assert rel3.id == 3


def test_relationship_is_directed(db, sample_nodes):
    """Test that relationships have direction (source -> target)."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    # Alice knows Bob
    rel = db.create_relationship(alice.id, bob.id, 'KNOWS')

    assert rel.source_id == alice.id
    assert rel.target_id == bob.id

    # Create opposite direction relationship
    rel2 = db.create_relationship(bob.id, alice.id, 'KNOWS')

    assert rel2.source_id == bob.id
    assert rel2.target_id == alice.id
    assert rel2.id != rel.id  # Different relationships


def test_multiple_relationships_same_nodes(db, sample_nodes):
    """Test that multiple relationships can exist between the same nodes."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel1 = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel2 = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel3 = db.create_relationship(alice.id, bob.id, 'FRIENDS_WITH')

    assert rel1.id != rel2.id
    assert rel2.id != rel3.id


def test_self_referential_relationship(db, sample_nodes):
    """Test that a node can have a relationship to itself."""
    alice = sample_nodes['alice']

    rel = db.create_relationship(alice.id, alice.id, 'MANAGES')

    assert rel.source_id == alice.id
    assert rel.target_id == alice.id


def test_create_relationship_invalid_source(db, sample_nodes):
    """Test that creating a relationship with invalid source raises error."""
    bob = sample_nodes['bob']

    with pytest.raises(NodeNotFoundError) as exc_info:
        db.create_relationship(999, bob.id, 'KNOWS')

    assert exc_info.value.node_id == 999


def test_create_relationship_invalid_target(db, sample_nodes):
    """Test that creating a relationship with invalid target raises error."""
    alice = sample_nodes['alice']

    with pytest.raises(NodeNotFoundError) as exc_info:
        db.create_relationship(alice.id, 999, 'KNOWS')

    assert exc_info.value.node_id == 999


def test_create_relationship_invalid_property_type(db, sample_nodes):
    """Test that invalid property types raise an error."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    with pytest.raises(InvalidPropertyError):
        db.create_relationship(
            alice.id, bob.id, 'KNOWS', properties={'tags': {'friend', 'coworker'}}
        )


def test_get_relationship(db, sample_nodes):
    """Test retrieving a relationship by ID."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    created = db.create_relationship(
        alice.id, bob.id, 'KNOWS', properties={'since': 2015}
    )

    retrieved = db.get_relationship(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.source_id == created.source_id
    assert retrieved.target_id == created.target_id
    assert retrieved.type == created.type
    assert retrieved.properties == created.properties


def test_get_nonexistent_relationship(db):
    """Test that getting a non-existent relationship returns None."""
    rel = db.get_relationship(999)
    assert rel is None


def test_delete_relationship(db, sample_nodes):
    """Test deleting a relationship."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel = db.create_relationship(alice.id, bob.id, 'KNOWS')

    success = db.delete_relationship(rel.id)

    assert success is True

    # Verify relationship is gone
    deleted = db.get_relationship(rel.id)
    assert deleted is None


def test_delete_nonexistent_relationship(db):
    """Test that deleting a non-existent relationship returns False."""
    success = db.delete_relationship(999)
    assert success is False


def test_delete_relationship_preserves_nodes(db, sample_nodes):
    """Test that deleting a relationship doesn't delete the nodes."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel = db.create_relationship(alice.id, bob.id, 'KNOWS')
    db.delete_relationship(rel.id)

    # Nodes should still exist
    assert db.get_node(alice.id) is not None
    assert db.get_node(bob.id) is not None


def test_delete_node_cascades_to_relationships(db, sample_nodes):
    """Test that deleting a node also deletes its relationships."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']
    company = sample_nodes['company']

    rel1 = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel2 = db.create_relationship(alice.id, company.id, 'WORKS_AT')
    rel3 = db.create_relationship(bob.id, company.id, 'WORKS_AT')

    # Delete Alice
    db.delete_node(alice.id)

    # Alice's relationships should be gone
    assert db.get_relationship(rel1.id) is None
    assert db.get_relationship(rel2.id) is None

    # Bob's relationship to company should still exist
    assert db.get_relationship(rel3.id) is not None


def test_delete_node_cascades_outgoing_and_incoming(db, sample_nodes):
    """Test that CASCADE works for both outgoing and incoming relationships."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel_out = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel_in = db.create_relationship(bob.id, alice.id, 'KNOWS')

    # Delete Alice
    db.delete_node(alice.id)

    # Both relationships should be gone
    assert db.get_relationship(rel_out.id) is None
    assert db.get_relationship(rel_in.id) is None


def test_relationship_types_are_preserved(db, sample_nodes):
    """Test that different relationship types are stored correctly."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']
    company = sample_nodes['company']

    rel1 = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel2 = db.create_relationship(alice.id, bob.id, 'FRIENDS_WITH')
    rel3 = db.create_relationship(alice.id, company.id, 'WORKS_AT')
    rel4 = db.create_relationship(bob.id, alice.id, 'REPORTS_TO')

    assert db.get_relationship(rel1.id).type == 'KNOWS'
    assert db.get_relationship(rel2.id).type == 'FRIENDS_WITH'
    assert db.get_relationship(rel3.id).type == 'WORKS_AT'
    assert db.get_relationship(rel4.id).type == 'REPORTS_TO'


def test_relationship_with_null_property(db, sample_nodes):
    """Test that None/null properties are handled correctly."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel = db.create_relationship(
        alice.id, bob.id, 'KNOWS', properties={'since': 2020, 'note': None}
    )

    retrieved = db.get_relationship(rel.id)
    assert retrieved.properties['note'] is None


def test_context_manager_with_relationships(db, sample_nodes):
    """Test that context manager commits relationship operations."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    with db:
        rel1 = db.create_relationship(alice.id, bob.id, 'KNOWS')
        rel2 = db.create_relationship(bob.id, alice.id, 'KNOWS')

    # Verify both relationships exist after context
    assert db.get_relationship(rel1.id) is not None
    assert db.get_relationship(rel2.id) is not None


def test_context_manager_rollback_relationships(db, sample_nodes):
    """Test that context manager rollback works for relationships."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    try:
        with db:
            rel = db.create_relationship(alice.id, bob.id, 'KNOWS')
            # Force an error
            raise ValueError("Test error")
    except ValueError:
        pass

    # Relationship should not exist due to rollback
    cursor = db.conn.execute("SELECT COUNT(*) FROM relationships")
    count = cursor.fetchone()[0]
    assert count == 0


def test_relationship_properties_are_independent(db, sample_nodes):
    """Test that relationship properties don't affect each other."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel1 = db.create_relationship(
        alice.id, bob.id, 'KNOWS', properties={'since': 2015}
    )
    rel2 = db.create_relationship(
        alice.id, bob.id, 'WORKS_WITH', properties={'project': 'GraphDB'}
    )

    retrieved1 = db.get_relationship(rel1.id)
    retrieved2 = db.get_relationship(rel2.id)

    assert retrieved1.properties == {'since': 2015}
    assert retrieved2.properties == {'project': 'GraphDB'}


def test_relationship_type_case_sensitive(db, sample_nodes):
    """Test that relationship types are case-sensitive."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel1 = db.create_relationship(alice.id, bob.id, 'KNOWS')
    rel2 = db.create_relationship(alice.id, bob.id, 'knows')

    assert db.get_relationship(rel1.id).type == 'KNOWS'
    assert db.get_relationship(rel2.id).type == 'knows'


def test_create_relationship_complex_properties(db, sample_nodes):
    """Test relationships with various property types."""
    alice = sample_nodes['alice']
    company = sample_nodes['company']

    properties = {
        'since': 2020,
        'position': 'Senior Engineer',
        'salary': 120000.50,
        'remote': True,
        'bonus': None,
    }

    rel = db.create_relationship(
        alice.id, company.id, 'WORKS_AT', properties=properties
    )

    retrieved = db.get_relationship(rel.id)
    assert retrieved.properties == properties
    assert isinstance(retrieved.properties['since'], int)
    assert isinstance(retrieved.properties['position'], str)
    assert isinstance(retrieved.properties['salary'], float)
    assert isinstance(retrieved.properties['remote'], bool)
    assert retrieved.properties['bonus'] is None


def test_relationship_repr(db, sample_nodes):
    """Test that relationship __repr__ is human-readable."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel = db.create_relationship(
        alice.id, bob.id, 'KNOWS', properties={'since': 2015}
    )

    repr_str = repr(rel)

    # Should contain source, target, type, and properties
    assert str(alice.id) in repr_str
    assert str(bob.id) in repr_str
    assert 'KNOWS' in repr_str
    assert '2015' in repr_str


def test_relationship_to_dict(db, sample_nodes):
    """Test that relationship to_dict() works correctly."""
    alice = sample_nodes['alice']
    bob = sample_nodes['bob']

    rel = db.create_relationship(
        alice.id, bob.id, 'KNOWS', properties={'since': 2015}
    )

    rel_dict = rel.to_dict()

    assert rel_dict['id'] == rel.id
    assert rel_dict['source_id'] == alice.id
    assert rel_dict['target_id'] == bob.id
    assert rel_dict['type'] == 'KNOWS'
    assert rel_dict['properties'] == {'since': 2015}
