"""Tests for pattern matching and query operations (Phase 4)."""

import pytest
from grafito import GrafitoDatabase, Node, NodeNotFoundError


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return GrafitoDatabase(':memory:')


@pytest.fixture
def sample_graph(db):
    """Create a sample graph for testing queries."""
    # Create nodes
    alice = db.create_node(
        labels=['Person', 'Employee'],
        properties={'name': 'Alice', 'age': 30, 'city': 'NYC'}
    )
    bob = db.create_node(
        labels=['Person', 'Employee'],
        properties={'name': 'Bob', 'age': 25, 'city': 'LA'}
    )
    charlie = db.create_node(
        labels=['Person'],
        properties={'name': 'Charlie', 'age': 35, 'city': 'NYC'}
    )
    diana = db.create_node(
        labels=['Person', 'Manager'],
        properties={'name': 'Diana', 'age': 40, 'city': 'NYC'}
    )
    techcorp = db.create_node(
        labels=['Company'],
        properties={'name': 'TechCorp', 'size': 'large'}
    )
    startup = db.create_node(
        labels=['Company'],
        properties={'name': 'StartupInc', 'size': 'small'}
    )

    # Create relationships
    db.create_relationship(alice.id, techcorp.id, 'WORKS_AT', {'since': 2020})
    db.create_relationship(bob.id, techcorp.id, 'WORKS_AT', {'since': 2021})
    db.create_relationship(charlie.id, startup.id, 'WORKS_AT', {'since': 2019})
    db.create_relationship(diana.id, techcorp.id, 'MANAGES', {'since': 2018})
    db.create_relationship(alice.id, bob.id, 'KNOWS', {'since': 2020})
    db.create_relationship(bob.id, charlie.id, 'KNOWS', {'since': 2019})
    db.create_relationship(diana.id, alice.id, 'MANAGES', {'since': 2020})

    return {
        'alice': alice,
        'bob': bob,
        'charlie': charlie,
        'diana': diana,
        'techcorp': techcorp,
        'startup': startup,
    }


# ============================================================================
# match_nodes() tests
# ============================================================================


def test_match_nodes_no_filters(db, sample_graph):
    """Test matching all nodes with no filters."""
    nodes = db.match_nodes()

    assert len(nodes) == 6


def test_match_nodes_by_single_label(db, sample_graph):
    """Test matching nodes by a single label."""
    persons = db.match_nodes(labels=['Person'])

    assert len(persons) == 4
    names = {node.properties['name'] for node in persons}
    assert names == {'Alice', 'Bob', 'Charlie', 'Diana'}


def test_match_nodes_by_multiple_labels(db, sample_graph):
    """Test matching nodes that have ALL specified labels."""
    employees = db.match_nodes(labels=['Person', 'Employee'])

    assert len(employees) == 2
    names = {node.properties['name'] for node in employees}
    assert names == {'Alice', 'Bob'}


def test_match_nodes_by_label_no_matches(db, sample_graph):
    """Test matching nodes with a label that doesn't exist."""
    nodes = db.match_nodes(labels=['Robot'])

    assert len(nodes) == 0


def test_match_nodes_by_properties(db, sample_graph):
    """Test matching nodes by properties."""
    nyc_nodes = db.match_nodes(properties={'city': 'NYC'})

    assert len(nyc_nodes) == 3
    names = {node.properties['name'] for node in nyc_nodes}
    assert names == {'Alice', 'Charlie', 'Diana'}


def test_match_nodes_by_multiple_properties(db, sample_graph):
    """Test matching nodes by multiple properties."""
    nodes = db.match_nodes(properties={'city': 'NYC', 'age': 30})

    assert len(nodes) == 1
    assert nodes[0].properties['name'] == 'Alice'


def test_match_nodes_by_label_and_properties(db, sample_graph):
    """Test matching nodes by both label and properties."""
    employees_in_nyc = db.match_nodes(
        labels=['Person', 'Employee'],
        properties={'city': 'NYC'}
    )

    assert len(employees_in_nyc) == 1
    assert employees_in_nyc[0].properties['name'] == 'Alice'


def test_match_nodes_property_not_found(db, sample_graph):
    """Test that nodes without a property don't match."""
    nodes = db.match_nodes(properties={'nonexistent': 'value'})

    assert len(nodes) == 0


def test_match_nodes_partial_property_match(db, sample_graph):
    """Test that partial property matches don't count."""
    # Only Diana has age 40
    nodes = db.match_nodes(properties={'age': 40})

    assert len(nodes) == 1
    assert nodes[0].properties['name'] == 'Diana'


def test_match_nodes_empty_result(db, sample_graph):
    """Test matching with impossible criteria."""
    nodes = db.match_nodes(labels=['Company'], properties={'age': 30})

    assert len(nodes) == 0


# ============================================================================
# match_relationships() tests
# ============================================================================


def test_match_relationships_no_filters(db, sample_graph):
    """Test matching all relationships with no filters."""
    rels = db.match_relationships()

    assert len(rels) == 7


def test_match_relationships_by_source(db, sample_graph):
    """Test matching relationships by source node."""
    alice = sample_graph['alice']
    rels = db.match_relationships(source_id=alice.id)

    assert len(rels) == 2
    types = {rel.type for rel in rels}
    assert types == {'WORKS_AT', 'KNOWS'}


def test_match_relationships_by_target(db, sample_graph):
    """Test matching relationships by target node."""
    techcorp = sample_graph['techcorp']
    rels = db.match_relationships(target_id=techcorp.id)

    assert len(rels) == 3
    types = {rel.type for rel in rels}
    assert types == {'WORKS_AT', 'MANAGES'}


def test_match_relationships_by_type(db, sample_graph):
    """Test matching relationships by type."""
    rels = db.match_relationships(rel_type='WORKS_AT')

    assert len(rels) == 3
    for rel in rels:
        assert rel.type == 'WORKS_AT'


def test_match_relationships_by_source_and_type(db, sample_graph):
    """Test matching relationships by source and type."""
    alice = sample_graph['alice']
    rels = db.match_relationships(source_id=alice.id, rel_type='KNOWS')

    assert len(rels) == 1
    assert rels[0].type == 'KNOWS'
    assert rels[0].target_id == sample_graph['bob'].id


def test_match_relationships_by_target_and_type(db, sample_graph):
    """Test matching relationships by target and type."""
    alice = sample_graph['alice']
    rels = db.match_relationships(target_id=alice.id, rel_type='MANAGES')

    assert len(rels) == 1
    assert rels[0].source_id == sample_graph['diana'].id


def test_match_relationships_by_source_and_target(db, sample_graph):
    """Test matching relationships by both source and target."""
    alice = sample_graph['alice']
    bob = sample_graph['bob']
    rels = db.match_relationships(source_id=alice.id, target_id=bob.id)

    assert len(rels) == 1
    assert rels[0].type == 'KNOWS'


def test_match_relationships_all_criteria(db, sample_graph):
    """Test matching relationships with all criteria specified."""
    alice = sample_graph['alice']
    techcorp = sample_graph['techcorp']
    rels = db.match_relationships(
        source_id=alice.id,
        target_id=techcorp.id,
        rel_type='WORKS_AT'
    )

    assert len(rels) == 1
    assert rels[0].properties['since'] == 2020


def test_match_relationships_no_matches(db, sample_graph):
    """Test matching relationships that don't exist."""
    alice = sample_graph['alice']
    rels = db.match_relationships(source_id=alice.id, rel_type='HATES')

    assert len(rels) == 0


# ============================================================================
# get_neighbors() tests
# ============================================================================


def test_get_neighbors_outgoing(db, sample_graph):
    """Test getting outgoing neighbors."""
    alice = sample_graph['alice']
    neighbors = db.get_neighbors(alice.id, direction='outgoing')

    assert len(neighbors) == 2
    names = {node.properties['name'] for node in neighbors}
    assert names == {'TechCorp', 'Bob'}


def test_get_neighbors_incoming(db, sample_graph):
    """Test getting incoming neighbors."""
    alice = sample_graph['alice']
    neighbors = db.get_neighbors(alice.id, direction='incoming')

    assert len(neighbors) == 1
    assert neighbors[0].properties['name'] == 'Diana'


def test_get_neighbors_both_directions(db, sample_graph):
    """Test getting neighbors in both directions."""
    alice = sample_graph['alice']
    neighbors = db.get_neighbors(alice.id, direction='both')

    assert len(neighbors) == 3
    names = {node.properties['name'] for node in neighbors}
    assert names == {'TechCorp', 'Bob', 'Diana'}


def test_get_neighbors_with_rel_type_filter(db, sample_graph):
    """Test getting neighbors filtered by relationship type."""
    alice = sample_graph['alice']
    neighbors = db.get_neighbors(alice.id, direction='outgoing', rel_type='KNOWS')

    assert len(neighbors) == 1
    assert neighbors[0].properties['name'] == 'Bob'


def test_get_neighbors_incoming_with_filter(db, sample_graph):
    """Test getting incoming neighbors with type filter."""
    alice = sample_graph['alice']
    neighbors = db.get_neighbors(alice.id, direction='incoming', rel_type='MANAGES')

    assert len(neighbors) == 1
    assert neighbors[0].properties['name'] == 'Diana'


def test_get_neighbors_both_with_filter(db, sample_graph):
    """Test getting neighbors in both directions with type filter."""
    techcorp = sample_graph['techcorp']
    neighbors = db.get_neighbors(techcorp.id, direction='both', rel_type='WORKS_AT')

    assert len(neighbors) == 2
    names = {node.properties['name'] for node in neighbors}
    assert names == {'Alice', 'Bob'}


def test_get_neighbors_no_neighbors(db, sample_graph):
    """Test node with no neighbors."""
    # Create isolated node
    isolated = db.create_node(labels=['Isolated'], properties={'name': 'Lonely'})
    neighbors = db.get_neighbors(isolated.id)

    assert len(neighbors) == 0


def test_get_neighbors_nonexistent_node(db):
    """Test that getting neighbors of non-existent node raises error."""
    with pytest.raises(NodeNotFoundError) as exc_info:
        db.get_neighbors(999)

    assert exc_info.value.node_id == 999


def test_get_neighbors_invalid_direction(db, sample_graph):
    """Test that invalid direction raises ValueError."""
    alice = sample_graph['alice']

    with pytest.raises(ValueError) as exc_info:
        db.get_neighbors(alice.id, direction='sideways')

    assert 'Invalid direction' in str(exc_info.value)
    assert 'sideways' in str(exc_info.value)


def test_get_neighbors_no_duplicates(db, sample_graph):
    """Test that neighbors are not duplicated when using 'both'."""
    # Create a node with multiple relationships to same target
    alice = sample_graph['alice']
    bob = sample_graph['bob']
    db.create_relationship(alice.id, bob.id, 'FRIENDS_WITH')

    neighbors = db.get_neighbors(alice.id, direction='outgoing')

    # Bob should appear only once despite multiple relationships
    names = [node.properties['name'] for node in neighbors]
    assert names.count('Bob') == 1


def test_get_neighbors_complex_graph(db, sample_graph):
    """Test neighbors in a more complex scenario."""
    techcorp = sample_graph['techcorp']
    incoming = db.get_neighbors(techcorp.id, direction='incoming')

    # TechCorp receives: Alice WORKS_AT, Bob WORKS_AT, Diana MANAGES
    assert len(incoming) == 3
    names = {node.properties['name'] for node in incoming}
    assert names == {'Alice', 'Bob', 'Diana'}


def test_match_nodes_returns_full_objects(db, sample_graph):
    """Test that matched nodes have all their data."""
    employees = db.match_nodes(labels=['Person', 'Employee'])

    for node in employees:
        assert node.id is not None
        assert len(node.labels) >= 2
        assert 'Person' in node.labels
        assert 'Employee' in node.labels
        assert 'name' in node.properties


def test_match_relationships_returns_full_objects(db, sample_graph):
    """Test that matched relationships have all their data."""
    rels = db.match_relationships(rel_type='WORKS_AT')

    for rel in rels:
        assert rel.id is not None
        assert rel.source_id is not None
        assert rel.target_id is not None
        assert rel.type == 'WORKS_AT'
        assert 'since' in rel.properties


def test_get_neighbors_returns_full_node_objects(db, sample_graph):
    """Test that neighbors are complete Node objects."""
    alice = sample_graph['alice']
    neighbors = db.get_neighbors(alice.id, direction='outgoing')

    for neighbor in neighbors:
        assert isinstance(neighbor, Node)
        assert neighbor.id is not None
        assert len(neighbor.labels) > 0
        assert 'name' in neighbor.properties
