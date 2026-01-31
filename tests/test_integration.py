"""Integration tests for Grafito graph database.

These tests verify end-to-end scenarios that combine multiple features
and operations to ensure the system works correctly as a whole.
"""

import pytest
from grafito import GrafitoDatabase


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return GrafitoDatabase(':memory:')


def test_social_network_scenario(db):
    """Test a complete social network scenario."""
    # Create users
    alice = db.create_node(
        labels=['Person', 'User'],
        properties={'name': 'Alice', 'age': 30}
    )
    bob = db.create_node(
        labels=['Person', 'User'],
        properties={'name': 'Bob', 'age': 25}
    )
    carol = db.create_node(
        labels=['Person', 'User'],
        properties={'name': 'Carol', 'age': 28}
    )

    # Create friendships
    db.create_relationship(alice.id, bob.id, 'FRIENDS_WITH', {'since': 2020})
    db.create_relationship(bob.id, carol.id, 'FRIENDS_WITH', {'since': 2021})

    # Query friends
    alice_friends = db.get_neighbors(alice.id, direction='outgoing', rel_type='FRIENDS_WITH')
    assert len(alice_friends) == 1
    assert alice_friends[0].properties['name'] == 'Bob'

    # Find path
    path = db.find_shortest_path(alice.id, carol.id)
    assert path is not None
    assert len(path) == 3
    assert path[0].properties['name'] == 'Alice'
    assert path[1].properties['name'] == 'Bob'
    assert path[2].properties['name'] == 'Carol'

    # Verify metadata
    assert db.get_node_count(label='User') == 3
    assert db.get_relationship_count(rel_type='FRIENDS_WITH') == 2


def test_company_hierarchy_scenario(db):
    """Test a company organizational structure scenario."""
    # Create company
    company = db.create_node(
        labels=['Company'],
        properties={'name': 'TechCorp'}
    )

    # Create departments
    engineering = db.create_node(
        labels=['Department'],
        properties={'name': 'Engineering'}
    )
    sales = db.create_node(
        labels=['Department'],
        properties={'name': 'Sales'}
    )

    db.create_relationship(engineering.id, company.id, 'PART_OF')
    db.create_relationship(sales.id, company.id, 'PART_OF')

    # Create employees
    ceo = db.create_node(
        labels=['Person', 'Employee', 'Executive'],
        properties={'name': 'CEO', 'salary': 500000}
    )
    eng_manager = db.create_node(
        labels=['Person', 'Employee', 'Manager'],
        properties={'name': 'Eng Manager', 'salary': 200000}
    )
    engineer = db.create_node(
        labels=['Person', 'Employee', 'Engineer'],
        properties={'name': 'Engineer', 'salary': 150000}
    )

    # Create org structure
    db.create_relationship(eng_manager.id, ceo.id, 'REPORTS_TO')
    db.create_relationship(engineer.id, eng_manager.id, 'REPORTS_TO')
    db.create_relationship(engineer.id, engineering.id, 'WORKS_IN')

    # Query hierarchy
    ceo_reports = db.get_neighbors(ceo.id, direction='incoming', rel_type='REPORTS_TO')
    assert len(ceo_reports) == 1
    assert ceo_reports[0].properties['name'] == 'Eng Manager'

    # Find all employees
    all_employees = db.match_nodes(labels=['Employee'])
    assert len(all_employees) == 3

    # Calculate total payroll
    total_payroll = sum(emp.properties['salary'] for emp in all_employees)
    assert total_payroll == 850000


def test_knowledge_graph_scenario(db):
    """Test a knowledge graph with concepts and relationships."""
    # Create concepts
    python = db.create_node(
        labels=['Concept', 'Language'],
        properties={'name': 'Python', 'year': 1991}
    )
    django = db.create_node(
        labels=['Concept', 'Framework'],
        properties={'name': 'Django', 'year': 2005}
    )
    flask = db.create_node(
        labels=['Concept', 'Framework'],
        properties={'name': 'Flask', 'year': 2010}
    )
    web = db.create_node(
        labels=['Concept', 'Domain'],
        properties={'name': 'Web Development'}
    )

    # Create relationships
    db.create_relationship(django.id, python.id, 'WRITTEN_IN')
    db.create_relationship(flask.id, python.id, 'WRITTEN_IN')
    db.create_relationship(django.id, web.id, 'USED_FOR')
    db.create_relationship(flask.id, web.id, 'USED_FOR')

    # Find all Python frameworks
    python_frameworks = db.get_neighbors(python.id, direction='incoming', rel_type='WRITTEN_IN')
    assert len(python_frameworks) == 2
    framework_names = {f.properties['name'] for f in python_frameworks}
    assert framework_names == {'Django', 'Flask'}

    # Find what Django is used for
    django_uses = db.get_neighbors(django.id, direction='outgoing', rel_type='USED_FOR')
    assert len(django_uses) == 1
    assert django_uses[0].properties['name'] == 'Web Development'


def test_transaction_rollback_scenario(db):
    """Test that transactions can be rolled back properly."""
    # Create initial data
    alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
    initial_count = db.get_node_count()

    # Try a transaction that will fail
    try:
        db.begin_transaction()
        bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
        # Force an error by trying to create relationship with non-existent node
        db.create_relationship(bob.id, 999, 'KNOWS')
        db.commit()
    except Exception:
        db.rollback()

    # Verify rollback worked - Bob should not exist
    final_count = db.get_node_count()
    assert final_count == initial_count

    # Verify only Alice exists
    all_persons = db.match_nodes(labels=['Person'])
    assert len(all_persons) == 1
    assert all_persons[0].properties['name'] == 'Alice'


def test_transaction_commit_scenario(db):
    """Test successful transaction commits."""
    with db:
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
        db.create_relationship(alice.id, bob.id, 'KNOWS')

    # Verify transaction committed
    assert db.get_node_count() == 2
    assert db.get_relationship_count() == 1

    # Verify nodes exist
    all_persons = db.match_nodes(labels=['Person'])
    assert len(all_persons) == 2


def test_complex_query_scenario(db):
    """Test complex queries involving multiple operations."""
    # Create a movie recommendation graph
    # Users
    alice = db.create_node(labels=['User'], properties={'name': 'Alice'})
    bob = db.create_node(labels=['User'], properties={'name': 'Bob'})
    carol = db.create_node(labels=['User'], properties={'name': 'Carol'})

    # Movies
    matrix = db.create_node(labels=['Movie'], properties={'title': 'The Matrix', 'year': 1999})
    inception = db.create_node(labels=['Movie'], properties={'title': 'Inception', 'year': 2010})
    interstellar = db.create_node(labels=['Movie'], properties={'title': 'Interstellar', 'year': 2014})

    # Ratings
    db.create_relationship(alice.id, matrix.id, 'RATED', {'score': 5})
    db.create_relationship(alice.id, inception.id, 'RATED', {'score': 5})
    db.create_relationship(bob.id, matrix.id, 'RATED', {'score': 5})
    db.create_relationship(bob.id, interstellar.id, 'RATED', {'score': 4})
    db.create_relationship(carol.id, inception.id, 'RATED', {'score': 4})

    # Find movies Alice rated
    alice_movies = db.get_neighbors(alice.id, direction='outgoing', rel_type='RATED')
    assert len(alice_movies) == 2
    alice_titles = {m.properties['title'] for m in alice_movies}
    assert alice_titles == {'The Matrix', 'Inception'}

    # Find users who rated The Matrix
    matrix_raters = db.get_neighbors(matrix.id, direction='incoming', rel_type='RATED')
    assert len(matrix_raters) == 2
    rater_names = {u.properties['name'] for u in matrix_raters}
    assert rater_names == {'Alice', 'Bob'}

    # Find movies from a specific year
    movies_2010 = db.match_nodes(labels=['Movie'], properties={'year': 2010})
    assert len(movies_2010) == 1
    assert movies_2010[0].properties['title'] == 'Inception'


def test_cascade_delete_scenario(db):
    """Test that deleting nodes cascades to relationships."""
    # Create a small graph
    alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
    bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
    carol = db.create_node(labels=['Person'], properties={'name': 'Carol'})

    db.create_relationship(alice.id, bob.id, 'KNOWS')
    db.create_relationship(bob.id, carol.id, 'KNOWS')
    db.create_relationship(alice.id, carol.id, 'KNOWS')

    initial_rel_count = db.get_relationship_count()
    assert initial_rel_count == 3

    # Delete Bob (should cascade delete his relationships)
    db.delete_node(bob.id)

    # Verify Bob is gone
    assert db.get_node_count() == 2

    # Verify his relationships are gone (2 relationships deleted)
    final_rel_count = db.get_relationship_count()
    assert final_rel_count == 1

    # Verify Alice-Carol relationship still exists
    remaining_rels = db.match_relationships(source_id=alice.id, target_id=carol.id)
    assert len(remaining_rels) == 1


def test_multiple_labels_scenario(db):
    """Test nodes with multiple labels and querying them."""
    # Create nodes with various label combinations
    db.create_node(
        labels=['Person', 'Employee', 'Manager'],
        properties={'name': 'Alice'}
    )
    db.create_node(
        labels=['Person', 'Employee'],
        properties={'name': 'Bob'}
    )
    db.create_node(
        labels=['Person'],
        properties={'name': 'Carol'}
    )
    db.create_node(
        labels=['Company'],
        properties={'name': 'TechCorp'}
    )

    # Query by single label
    persons = db.match_nodes(labels=['Person'])
    assert len(persons) == 3

    employees = db.match_nodes(labels=['Employee'])
    assert len(employees) == 2

    managers = db.match_nodes(labels=['Manager'])
    assert len(managers) == 1

    # Query by multiple labels (must have ALL)
    employee_managers = db.match_nodes(labels=['Employee', 'Manager'])
    assert len(employee_managers) == 1
    assert employee_managers[0].properties['name'] == 'Alice'

    # Query with label and property
    person_employees = db.match_nodes(
        labels=['Person', 'Employee'],
        properties={'name': 'Bob'}
    )
    assert len(person_employees) == 1


def test_label_management_scenario(db):
    """Test adding and removing labels dynamically."""
    node = db.create_node(labels=['Person'], properties={'name': 'Alice'})

    # Verify initial label
    assert node.labels == ['Person']

    # Add labels
    db.add_labels(node.id, ['Employee', 'Manager'])
    updated_node = db.get_node(node.id)
    assert set(updated_node.labels) == {'Person', 'Employee', 'Manager'}

    # Remove a label
    db.remove_labels(node.id, ['Manager'])
    updated_node = db.get_node(node.id)
    assert set(updated_node.labels) == {'Person', 'Employee'}

    # Node should still be queryable by remaining labels
    employees = db.match_nodes(labels=['Employee'])
    assert len(employees) == 1
    assert employees[0].id == node.id


def test_property_update_scenario(db):
    """Test updating properties on nodes and relationships."""
    # Create node
    node = db.create_node(
        labels=['Person'],
        properties={'name': 'Alice', 'age': 30}
    )

    # Update properties (merge)
    db.update_node_properties(node.id, {'age': 31, 'city': 'NYC'})

    # Verify merge
    updated_node = db.get_node(node.id)
    assert updated_node.properties['name'] == 'Alice'  # Original preserved
    assert updated_node.properties['age'] == 31  # Updated
    assert updated_node.properties['city'] == 'NYC'  # Added

    # Create relationship
    bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
    rel = db.create_relationship(
        node.id, bob.id, 'KNOWS',
        properties={'since': 2020}
    )

    # Verify relationship properties
    retrieved_rel = db.get_relationship(rel.id)
    assert retrieved_rel.properties['since'] == 2020


def test_cyclic_graph_scenario(db):
    """Test graph with cycles."""
    # Create cycle: A -> B -> C -> A
    a = db.create_node(labels=['Node'], properties={'name': 'A'})
    b = db.create_node(labels=['Node'], properties={'name': 'B'})
    c = db.create_node(labels=['Node'], properties={'name': 'C'})

    db.create_relationship(a.id, b.id, 'NEXT')
    db.create_relationship(b.id, c.id, 'NEXT')
    db.create_relationship(c.id, a.id, 'NEXT')

    # Find path (should handle cycle)
    path = db.find_path(a.id, c.id)
    assert path is not None
    assert len(path) == 3
    assert path[0].properties['name'] == 'A'
    assert path[2].properties['name'] == 'C'

    # Shortest path should also work
    shortest = db.find_shortest_path(a.id, c.id)
    assert shortest is not None
    assert len(shortest) == 3


def test_metadata_consistency_scenario(db):
    """Test that metadata queries return consistent results."""
    # Initially empty
    assert db.get_node_count() == 0
    assert db.get_relationship_count() == 0
    assert len(db.get_all_labels()) == 0
    assert len(db.get_all_relationship_types()) == 0

    # Create data
    alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
    bob = db.create_node(labels=['Person', 'Employee'], properties={'name': 'Bob'})
    db.create_relationship(alice.id, bob.id, 'KNOWS')
    db.create_relationship(alice.id, bob.id, 'WORKS_WITH')

    # Verify counts
    assert db.get_node_count() == 2
    assert db.get_node_count(label='Person') == 2
    assert db.get_node_count(label='Employee') == 1
    assert db.get_relationship_count() == 2
    assert db.get_relationship_count(rel_type='KNOWS') == 1

    # Verify labels and types
    all_labels = db.get_all_labels()
    assert set(all_labels) == {'Person', 'Employee'}

    all_types = db.get_all_relationship_types()
    assert set(all_types) == {'KNOWS', 'WORKS_WITH'}

    # Delete node and verify counts update
    db.delete_node(bob.id)
    assert db.get_node_count() == 1
    assert db.get_relationship_count() == 0  # Cascade deleted


def test_empty_graph_queries(db):
    """Test queries on empty graph."""
    # All queries should work on empty graph
    assert db.match_nodes() == []
    assert db.match_nodes(labels=['Person']) == []
    assert db.match_relationships() == []
    assert db.get_node_count() == 0
    assert db.get_relationship_count() == 0
    assert db.get_all_labels() == []
    assert db.get_all_relationship_types() == []


def test_large_graph_scenario(db):
    """Test performance with a moderately large graph."""
    # Create 100 nodes
    nodes = []
    for i in range(100):
        node = db.create_node(
            labels=['Node'],
            properties={'id': i, 'name': f'Node{i}'}
        )
        nodes.append(node)

    # Create relationships (each node connects to next)
    for i in range(99):
        db.create_relationship(nodes[i].id, nodes[i + 1].id, 'NEXT')

    # Verify counts
    assert db.get_node_count() == 100
    assert db.get_relationship_count() == 99

    # Find shortest path (should be 100 nodes long)
    path = db.find_shortest_path(nodes[0].id, nodes[99].id)
    assert path is not None
    assert len(path) == 100

    # Query specific nodes
    specific = db.match_nodes(labels=['Node'], properties={'id': 50})
    assert len(specific) == 1
    assert specific[0].properties['name'] == 'Node50'
