"""Tests for graph traversal and path finding (Phase 5)."""

import pytest
from grafito import GrafitoDatabase, NodeNotFoundError
from grafito.query import PathFinder


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return GrafitoDatabase(':memory:')


@pytest.fixture
def linear_graph(db):
    """Create a linear graph: A -> B -> C -> D -> E."""
    nodes = {}
    for name in ['A', 'B', 'C', 'D', 'E']:
        node = db.create_node(labels=['Node'], properties={'name': name})
        nodes[name] = node

    # Create linear path
    db.create_relationship(nodes['A'].id, nodes['B'].id, 'NEXT')
    db.create_relationship(nodes['B'].id, nodes['C'].id, 'NEXT')
    db.create_relationship(nodes['C'].id, nodes['D'].id, 'NEXT')
    db.create_relationship(nodes['D'].id, nodes['E'].id, 'NEXT')

    return nodes


@pytest.fixture
def complex_graph(db):
    """Create a more complex graph with multiple paths.

    Graph structure:
        A -> B -> D -> F
        |    |    |
        v    v    v
        C ---+--> E

    This creates multiple paths from A to E and from A to F.
    """
    nodes = {}
    for name in ['A', 'B', 'C', 'D', 'E', 'F']:
        node = db.create_node(labels=['Node'], properties={'name': name})
        nodes[name] = node

    # Create multiple paths
    db.create_relationship(nodes['A'].id, nodes['B'].id, 'CONNECTS')
    db.create_relationship(nodes['A'].id, nodes['C'].id, 'CONNECTS')
    db.create_relationship(nodes['B'].id, nodes['D'].id, 'CONNECTS')
    db.create_relationship(nodes['B'].id, nodes['E'].id, 'CONNECTS')
    db.create_relationship(nodes['C'].id, nodes['E'].id, 'CONNECTS')
    db.create_relationship(nodes['D'].id, nodes['E'].id, 'CONNECTS')
    db.create_relationship(nodes['D'].id, nodes['F'].id, 'CONNECTS')

    return nodes


@pytest.fixture
def cyclic_graph(db):
    """Create a graph with cycles: A -> B -> C -> A (and other connections)."""
    nodes = {}
    for name in ['A', 'B', 'C', 'D']:
        node = db.create_node(labels=['Node'], properties={'name': name})
        nodes[name] = node

    # Create cycle
    db.create_relationship(nodes['A'].id, nodes['B'].id, 'NEXT')
    db.create_relationship(nodes['B'].id, nodes['C'].id, 'NEXT')
    db.create_relationship(nodes['C'].id, nodes['A'].id, 'NEXT')  # Cycle
    db.create_relationship(nodes['B'].id, nodes['D'].id, 'NEXT')

    return nodes


# ============================================================================
# find_shortest_path() tests (BFS)
# ============================================================================


def test_find_shortest_path_direct_connection(db, linear_graph):
    """Test shortest path with direct connection."""
    path = db.find_shortest_path(linear_graph['A'].id, linear_graph['B'].id)

    assert path is not None
    assert len(path) == 2
    assert path[0].properties['name'] == 'A'
    assert path[1].properties['name'] == 'B'


def test_find_shortest_path_multiple_hops(db, linear_graph):
    """Test shortest path with multiple hops."""
    path = db.find_shortest_path(linear_graph['A'].id, linear_graph['E'].id)

    assert path is not None
    assert len(path) == 5
    names = [node.properties['name'] for node in path]
    assert names == ['A', 'B', 'C', 'D', 'E']


def test_find_shortest_path_same_node(db, linear_graph):
    """Test shortest path when source equals target."""
    path = db.find_shortest_path(linear_graph['A'].id, linear_graph['A'].id)

    assert path is not None
    assert len(path) == 1
    assert path[0].properties['name'] == 'A'


def test_find_shortest_path_no_path(db, linear_graph):
    """Test shortest path when no path exists."""
    # E doesn't connect back to A (linear graph)
    path = db.find_shortest_path(linear_graph['E'].id, linear_graph['A'].id)

    assert path is None


def test_find_shortest_path_chooses_shortest(db, complex_graph):
    """Test that BFS finds the shortest path when multiple paths exist."""
    # From A to E, there are multiple paths:
    # - A -> C -> E (2 hops)
    # - A -> B -> E (2 hops)
    # - A -> B -> D -> E (3 hops)
    path = db.find_shortest_path(complex_graph['A'].id, complex_graph['E'].id)

    assert path is not None
    assert len(path) == 3  # 2 hops = 3 nodes
    # Should be one of the 2-hop paths
    names = [node.properties['name'] for node in path]
    assert names[0] == 'A'
    assert names[2] == 'E'
    # Middle node should be either B or C
    assert names[1] in ['B', 'C']


def test_find_shortest_path_handles_cycles(db, cyclic_graph):
    """Test that BFS handles cycles correctly."""
    path = db.find_shortest_path(cyclic_graph['A'].id, cyclic_graph['D'].id)

    assert path is not None
    # Shortest path: A -> B -> D (3 nodes, 2 hops)
    assert len(path) == 3
    names = [node.properties['name'] for node in path]
    assert names == ['A', 'B', 'D']


def test_find_shortest_path_nonexistent_source(db, linear_graph):
    """Test that nonexistent source raises error."""
    with pytest.raises(NodeNotFoundError) as exc_info:
        db.find_shortest_path(999, linear_graph['A'].id)

    assert exc_info.value.node_id == 999


def test_find_shortest_path_nonexistent_target(db, linear_graph):
    """Test that nonexistent target raises error."""
    with pytest.raises(NodeNotFoundError) as exc_info:
        db.find_shortest_path(linear_graph['A'].id, 999)

    assert exc_info.value.node_id == 999


# ============================================================================
# find_path() tests (DFS with depth limit)
# ============================================================================


def test_find_path_direct_connection(db, linear_graph):
    """Test finding any path with direct connection."""
    path = db.find_path(linear_graph['A'].id, linear_graph['B'].id)

    assert path is not None
    assert len(path) == 2
    assert path[0].properties['name'] == 'A'
    assert path[1].properties['name'] == 'B'


def test_find_path_multiple_hops(db, linear_graph):
    """Test finding any path with multiple hops."""
    path = db.find_path(linear_graph['A'].id, linear_graph['E'].id)

    assert path is not None
    assert len(path) >= 2
    assert path[0].properties['name'] == 'A'
    assert path[-1].properties['name'] == 'E'


def test_find_path_same_node(db, linear_graph):
    """Test finding path when source equals target."""
    path = db.find_path(linear_graph['A'].id, linear_graph['A'].id)

    assert path is not None
    assert len(path) == 1
    assert path[0].properties['name'] == 'A'


def test_find_path_no_path(db, linear_graph):
    """Test finding path when no path exists."""
    path = db.find_path(linear_graph['E'].id, linear_graph['A'].id)

    assert path is None


def test_find_path_with_depth_limit(db, linear_graph):
    """Test finding path with depth limit."""
    # Try to reach E from A with max 2 hops (should fail)
    path = db.find_path(linear_graph['A'].id, linear_graph['E'].id, max_depth=2)

    assert path is None  # Need 4 hops, limit is 2

    # Try with max 4 hops (should succeed)
    path = db.find_path(linear_graph['A'].id, linear_graph['E'].id, max_depth=4)

    assert path is not None
    assert path[0].properties['name'] == 'A'
    assert path[-1].properties['name'] == 'E'


def test_find_path_depth_limit_exact(db, linear_graph):
    """Test path finding with exact depth limit."""
    # A to D requires exactly 3 hops
    path = db.find_path(linear_graph['A'].id, linear_graph['D'].id, max_depth=3)

    assert path is not None
    assert len(path) == 4
    names = [node.properties['name'] for node in path]
    assert names == ['A', 'B', 'C', 'D']


def test_find_path_handles_cycles(db, cyclic_graph):
    """Test that DFS handles cycles correctly."""
    path = db.find_path(cyclic_graph['A'].id, cyclic_graph['D'].id)

    assert path is not None
    assert path[0].properties['name'] == 'A'
    assert path[-1].properties['name'] == 'D'


def test_find_path_nonexistent_source(db, linear_graph):
    """Test that nonexistent source raises error."""
    with pytest.raises(NodeNotFoundError) as exc_info:
        db.find_path(999, linear_graph['A'].id)

    assert exc_info.value.node_id == 999


def test_find_path_nonexistent_target(db, linear_graph):
    """Test that nonexistent target raises error."""
    with pytest.raises(NodeNotFoundError) as exc_info:
        db.find_path(linear_graph['A'].id, 999)

    assert exc_info.value.node_id == 999


# ============================================================================
# PathFinder class direct tests
# ============================================================================


def test_pathfinder_bfs_shortest_path(db, complex_graph):
    """Test PathFinder BFS directly."""
    finder = PathFinder(db)
    path = finder.bfs_shortest_path(complex_graph['A'].id, complex_graph['F'].id)

    assert path is not None
    # Shortest path: A -> B -> D -> F (4 nodes, 3 hops)
    assert len(path) == 4
    names = [node.properties['name'] for node in path]
    assert names == ['A', 'B', 'D', 'F']


def test_pathfinder_dfs_find_path(db, complex_graph):
    """Test PathFinder DFS directly."""
    finder = PathFinder(db)
    path = finder.dfs_find_path(complex_graph['A'].id, complex_graph['E'].id)

    assert path is not None
    assert path[0].properties['name'] == 'A'
    assert path[-1].properties['name'] == 'E'


def test_pathfinder_dfs_with_max_depth(db, linear_graph):
    """Test PathFinder DFS with max depth."""
    finder = PathFinder(db)

    # Should fail with depth 2
    path = finder.dfs_find_path(linear_graph['A'].id, linear_graph['E'].id, max_depth=2)
    assert path is None

    # Should succeed with depth 5
    path = finder.dfs_find_path(linear_graph['A'].id, linear_graph['E'].id, max_depth=5)
    assert path is not None


def test_pathfinder_find_all_paths(db, complex_graph):
    """Test PathFinder find_all_paths method."""
    finder = PathFinder(db)
    all_paths = finder.find_all_paths(complex_graph['A'].id, complex_graph['E'].id)

    # There are multiple paths from A to E
    assert len(all_paths) > 1

    # All paths should start with A and end with E
    for path in all_paths:
        assert path[0].properties['name'] == 'A'
        assert path[-1].properties['name'] == 'E'


def test_pathfinder_find_all_paths_with_depth_limit(db, complex_graph):
    """Test find_all_paths with depth limit."""
    finder = PathFinder(db)

    # Find all paths with max 2 hops
    all_paths = finder.find_all_paths(
        complex_graph['A'].id, complex_graph['E'].id, max_depth=2
    )

    # Should find the 2-hop paths only
    assert len(all_paths) >= 1
    for path in all_paths:
        assert len(path) <= 3  # 2 hops = 3 nodes


# ============================================================================
# Edge cases and special scenarios
# ============================================================================


def test_isolated_nodes_no_path(db):
    """Test that isolated nodes have no path between them."""
    node1 = db.create_node(labels=['Isolated'], properties={'name': 'Node1'})
    node2 = db.create_node(labels=['Isolated'], properties={'name': 'Node2'})

    path = db.find_shortest_path(node1.id, node2.id)
    assert path is None

    path = db.find_path(node1.id, node2.id)
    assert path is None


def test_self_loop(db):
    """Test path finding with self-referential relationship."""
    node = db.create_node(labels=['Node'], properties={'name': 'Self'})
    db.create_relationship(node.id, node.id, 'SELF_REF')

    # Path to itself should return single node
    path = db.find_shortest_path(node.id, node.id)
    assert path is not None
    assert len(path) == 1


def test_bidirectional_relationship(db):
    """Test path finding with bidirectional relationships."""
    node_a = db.create_node(labels=['Node'], properties={'name': 'A'})
    node_b = db.create_node(labels=['Node'], properties={'name': 'B'})

    # Create bidirectional connection
    db.create_relationship(node_a.id, node_b.id, 'CONNECTS')
    db.create_relationship(node_b.id, node_a.id, 'CONNECTS')

    # Should find path both ways
    path_ab = db.find_shortest_path(node_a.id, node_b.id)
    assert path_ab is not None
    assert len(path_ab) == 2

    path_ba = db.find_shortest_path(node_b.id, node_a.id)
    assert path_ba is not None
    assert len(path_ba) == 2


def test_large_depth_limit(db, linear_graph):
    """Test that very large depth limit doesn't cause issues."""
    path = db.find_path(
        linear_graph['A'].id, linear_graph['E'].id, max_depth=1000
    )

    assert path is not None
    assert len(path) == 5


def test_path_returns_node_objects(db, linear_graph):
    """Test that paths return proper Node objects with all data."""
    path = db.find_shortest_path(linear_graph['A'].id, linear_graph['C'].id)

    assert path is not None
    for node in path:
        assert node.id is not None
        assert len(node.labels) > 0
        assert 'name' in node.properties
        assert hasattr(node, 'to_dict')


def test_complex_graph_multiple_shortest_paths(db):
    """Test graph where multiple shortest paths exist."""
    # Create diamond-shaped graph
    #     B
    #    / \
    #   A   D
    #    \ /
    #     C
    nodes = {}
    for name in ['A', 'B', 'C', 'D']:
        node = db.create_node(labels=['Node'], properties={'name': name})
        nodes[name] = node

    db.create_relationship(nodes['A'].id, nodes['B'].id, 'PATH')
    db.create_relationship(nodes['A'].id, nodes['C'].id, 'PATH')
    db.create_relationship(nodes['B'].id, nodes['D'].id, 'PATH')
    db.create_relationship(nodes['C'].id, nodes['D'].id, 'PATH')

    path = db.find_shortest_path(nodes['A'].id, nodes['D'].id)

    # Both paths are length 3 (2 hops)
    assert path is not None
    assert len(path) == 3
    assert path[0].properties['name'] == 'A'
    assert path[-1].properties['name'] == 'D'
    # Middle node should be B or C
    assert path[1].properties['name'] in ['B', 'C']
