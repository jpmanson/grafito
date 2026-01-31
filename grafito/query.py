"""Graph traversal and path finding algorithms for Grafito."""

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .database import GrafitoDatabase
    from .models import Node


class PathFinder:
    """Implements graph traversal algorithms for finding paths between nodes.

    This class provides BFS (Breadth-First Search) for shortest path finding
    and DFS (Depth-First Search) for general path finding with depth limits.
    """

    def __init__(self, db: 'GrafitoDatabase'):
        """Initialize PathFinder with a database connection.

        Args:
            db: GrafitoDatabase instance to query
        """
        self.db = db

    def bfs_shortest_path(
        self, source_id: int, target_id: int
    ) -> list['Node'] | None:
        """Find the shortest path between two nodes using BFS.

        Breadth-First Search guarantees finding the shortest path (minimum number
        of hops) in an unweighted graph.

        Args:
            source_id: Starting node ID
            target_id: Target node ID

        Returns:
            List of Node objects representing the path from source to target,
            or None if no path exists.

        Example:
            If the path is A -> B -> C, returns [Node(A), Node(B), Node(C)]
        """
        # Handle special case: source is target
        if source_id == target_id:
            node = self.db.get_node(source_id)
            return [node] if node else None

        # BFS initialization
        # Queue contains tuples of (current_node_id, path_so_far)
        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current_id, path = queue.popleft()

            # Get all outgoing neighbors
            neighbors = self.db.get_neighbors(current_id, direction='outgoing')

            for neighbor in neighbors:
                if neighbor.id in visited:
                    continue

                # Build new path including this neighbor
                new_path = path + [neighbor.id]

                # Check if we reached the target
                if neighbor.id == target_id:
                    # Convert node IDs to Node objects
                    return [self.db.get_node(nid) for nid in new_path]

                # Mark as visited and add to queue
                visited.add(neighbor.id)
                queue.append((neighbor.id, new_path))

        # No path found
        return None

    def dfs_find_path(
        self, source_id: int, target_id: int, max_depth: int = None
    ) -> list['Node'] | None:
        """Find any path between two nodes using DFS with optional depth limit.

        Depth-First Search explores as far as possible along each branch before
        backtracking. This may not find the shortest path, but can be useful
        for finding any path or exploring with depth constraints.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            max_depth: Maximum number of relationships to traverse (None for unlimited)

        Returns:
            List of Node objects representing a path from source to target,
            or None if no path exists within the depth limit.

        Example:
            If the path is A -> B -> C, returns [Node(A), Node(B), Node(C)]
        """
        # Handle special case: source is target
        if source_id == target_id:
            node = self.db.get_node(source_id)
            return [node] if node else None

        # Use a helper function for recursive DFS
        visited = set()

        def dfs_recursive(current_id: int, path: list[int], depth: int) -> list[int] | None:
            """Recursive DFS helper function.

            Args:
                current_id: Current node being explored
                path: Current path taken (list of node IDs)
                depth: Current depth (number of edges traversed)

            Returns:
                Path as list of node IDs if found, None otherwise
            """
            # Check depth limit
            if max_depth is not None and depth >= max_depth:
                return None

            # Mark current node as visited
            visited.add(current_id)

            # Get outgoing neighbors
            neighbors = self.db.get_neighbors(current_id, direction='outgoing')

            for neighbor in neighbors:
                # Skip if already visited (avoid cycles)
                if neighbor.id in visited:
                    continue

                # Build new path
                new_path = path + [neighbor.id]

                # Check if we reached the target
                if neighbor.id == target_id:
                    return new_path

                # Recursively explore this neighbor
                result = dfs_recursive(neighbor.id, new_path, depth + 1)
                if result is not None:
                    return result

            # Backtrack: unmark as visited to allow other paths
            visited.remove(current_id)
            return None

        # Start DFS from source
        path_ids = dfs_recursive(source_id, [source_id], 0)

        if path_ids:
            # Convert node IDs to Node objects
            return [self.db.get_node(nid) for nid in path_ids]

        return None

    def find_all_paths(
        self, source_id: int, target_id: int, max_depth: int = None
    ) -> list[list['Node']]:
        """Find all paths between two nodes (advanced, not required for Phase 5).

        This method finds all possible paths from source to target, optionally
        limited by max_depth. Can be expensive on large graphs.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            max_depth: Maximum number of relationships to traverse (None for unlimited)

        Returns:
            List of paths, where each path is a list of Node objects.
            Returns empty list if no paths exist.

        Note:
            This method is provided for completeness but not required for the
            Phase 5 implementation plan.
        """
        if source_id == target_id:
            node = self.db.get_node(source_id)
            return [[node]] if node else []

        all_paths = []

        def dfs_all_paths(current_id: int, path: list[int], visited: set[int], depth: int):
            """Recursive DFS to find all paths."""
            if max_depth is not None and depth >= max_depth:
                return

            neighbors = self.db.get_neighbors(current_id, direction='outgoing')

            for neighbor in neighbors:
                if neighbor.id in visited:
                    continue

                new_path = path + [neighbor.id]

                if neighbor.id == target_id:
                    # Found a complete path
                    all_paths.append(new_path)
                else:
                    # Continue searching
                    new_visited = visited | {neighbor.id}
                    dfs_all_paths(neighbor.id, new_path, new_visited, depth + 1)

        # Start search
        dfs_all_paths(source_id, [source_id], {source_id}, 0)

        # Convert paths to Node objects
        return [
            [self.db.get_node(nid) for nid in path_ids]
            for path_ids in all_paths
        ]
