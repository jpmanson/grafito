# Graph Traversal

Graph traversal means navigating through the graph by following relationships.

## Neighbors

Get directly connected nodes.

### Basic Neighbors

```python
# Get all outgoing neighbors
friends = db.get_neighbors(alice.id, direction='outgoing')

# Get all incoming neighbors (who points to Alice)
followers = db.get_neighbors(alice.id, direction='incoming')

# Get neighbors in both directions
all_neighbors = db.get_neighbors(alice.id, direction='both')
```

### Filtered by Relationship Type

```python
# Only coworkers
coworkers = db.get_neighbors(
    alice.id,
    direction='outgoing',
    rel_type='WORKS_WITH'
)

# Only direct reports
reports = db.get_neighbors(
    manager.id,
    direction='outgoing',
    rel_type='MANAGES'
)

# Only managers (incoming)
managers = db.get_neighbors(
    employee.id,
    direction='incoming',
    rel_type='MANAGES'
)
```

## Path Finding

Find routes between nodes.

### Shortest Path (BFS)

Breadth-first search finds the shortest path in terms of number of hops:

```python
# Find shortest path
path = db.find_shortest_path(alice.id, bob.id)

if path:
    print(f"Path length: {len(path)} nodes")
    for node in path:
        print(f"  -> {node.properties['name']}")
else:
    print("No path found")

# Example output:
# Path length: 3 nodes
#   -> Alice
#   -> Charlie
#   -> Bob
```

### Any Path (DFS)

Depth-first search finds any path with optional depth limit:

```python
# Find any path with max depth
path = db.find_path(alice.id, bob.id, max_depth=5)

if path:
    names = [n.properties['name'] for n in path]
    print(f"Path: {' -> '.join(names)}")
```

### Path with Cypher

More complex path queries using Cypher:

```python
# Shortest path with specific relationship type
results = db.execute("""
    MATCH p = shortestPath(
        (a:Person {name: 'Alice'})-[:KNOWS*1..5]->(b:Person {name: 'Bob'})
    )
    RETURN p, length(p) as hops
""")

# All shortest paths
results = db.execute("""
    MATCH p = allShortestPaths(
        (a:Person {name: 'Alice'})-[:KNOWS*1..5]->(b:Person {name: 'Bob'})
    )
    RETURN p
""")
```

## Variable-Length Patterns

Match patterns with variable path lengths.

### Basic Variable Length

```python
# Friends of friends (2 hops)
fof = db.execute("""
    MATCH (a:Person {name: 'Alice'})-[:KNOWS*2]->(fof:Person)
    WHERE fof <> a
    RETURN DISTINCT fof.name
""")

# 1 to 3 hops
network = db.execute("""
    MATCH (a:Person {name: 'Alice'})-[:KNOWS*1..3]->(other:Person)
    WHERE other <> a
    RETURN other.name, length(p) as distance
""")
```

### Unbounded Paths

Use with caution - always configure a maximum:

```python
# Configure max hops when creating database
db = GrafitoDatabase(':memory:', cypher_max_hops=5)

# This uses the configured max
db.execute("MATCH (a)-[:KNOWS*..]->(b) RETURN b")
```

## Traversal Strategies

### Top-Down Hierarchy

```python
def get_all_reports(db, manager_id, max_depth=5):
    """Get all employees in reporting chain."""
    results = db.execute("""
        MATCH (mgr:Person {id: $manager_id})<-[:REPORTS_TO*1..$max_depth]-(emp:Person)
        RETURN emp, length(p) as level
    """, {'manager_id': manager_id, 'max_depth': max_depth})
    
    return [(row['emp'], row['level']) for row in results]
```

### Bottom-Up Ancestry

```python
def get_management_chain(db, employee_id):
    """Get chain of command up to CEO."""
    results = db.execute("""
        MATCH (emp:Person {id: $employee_id})-[:REPORTS_TO*]->(manager:Person)
        RETURN manager.name
    """, {'employee_id': employee_id})
    
    return [row['manager.name'] for row in results]
```

### Circular Detection

```python
def has_circular_reference(db, node_id, rel_type):
    """Check if node participates in a cycle."""
    try:
        results = db.execute("""
            MATCH (n {id: $node_id})-[:$rel_type*]->(n)
            RETURN count(*) as cycles
        """, {'node_id': node_id, 'rel_type': rel_type})
        return results[0]['cycles'] > 0
    except:
        return False
```

## Common Algorithms

### Degree Centrality

```python
def get_most_connected(db, label='Person', limit=10):
    """Find nodes with most connections."""
    results = db.execute("""
        MATCH (n:$label)-[r]-()
        RETURN n.name, count(r) as degree
        ORDER BY degree DESC
        LIMIT $limit
    """, {'label': label, 'limit': limit})
    
    return results
```

### Common Neighbors

```python
def common_neighbors(db, node1_id, node2_id):
    """Find nodes connected to both."""
    results = db.execute("""
        MATCH (n1 {id: $id1})-->(common)<--(n2 {id: $id2})
        RETURN DISTINCT common
    """, {'id1': node1_id, 'id2': node2_id})
    
    return [row['common'] for row in results]
```

### Graph Diameter

```python
def estimate_diameter(db):
    """Estimate longest shortest path in graph."""
    results = db.execute("""
        MATCH (a:Person), (b:Person)
        WHERE a <> b
        MATCH p = shortestPath((a)-[:KNOWS*]->(b))
        RETURN max(length(p)) as diameter
    """)
    
    return results[0]['diameter'] if results else 0
```

## Performance Considerations

### 1. Limit Path Length

```python
# Good: Bounded search
results = db.execute("MATCH (a)-[:KNOWS*1..3]->(b) RETURN b")

# Risky: Unbounded
results = db.execute("MATCH (a)-[:KNOWS*..]->(b) RETURN b")  # Uses default max
```

### 2. Use Indexes

```python
# Create index for faster lookups
db.create_node_index('Person', 'name')

# Query uses index
results = db.execute("MATCH (n:Person {name: 'Alice'})-[:KNOWS]->(b) RETURN b")
```

### 3. Filter Early

```python
# Good: Filter before expanding
results = db.execute("""
    MATCH (n:Person {active: true})-[:KNOWS]->(b)
    WHERE n.created_at > $date
    RETURN b
""")

# Less efficient: Expand then filter
results = db.execute("""
    MATCH (n)-[:KNOWS]->(b)
    WHERE n:Person AND n.active = true AND n.created_at > $date
    RETURN b
""")
```

## Examples

### Recommendation Engine

```python
def recommend_friends(db, user_id):
    """Friend of friends who aren't already friends."""
    results = db.execute("""
        MATCH (me:Person {id: $user_id})-[:KNOWS]->(friend)-[:KNOWS]->(fof)
        WHERE fof <> me
          AND NOT (me)-[:KNOWS]->(fof)
        RETURN fof.name, count(friend) as mutual_friends
        ORDER BY mutual_friends DESC
        LIMIT 10
    """, {'user_id': user_id})
    
    return results
```

### Supply Chain

```python
def get_suppliers(db, product_id, tier=2):
    """Get n-tier suppliers."""
    results = db.execute("""
        MATCH (p:Product {id: $product_id})-[:REQUIRES*1..$tier]->(s:Supplier)
        RETURN DISTINCT s, min(length(p)) as tier
    """, {'product_id': product_id, 'tier': tier})
    
    return results
```

### Content Navigation

```python
def related_content(db, article_id):
    """Find content through multiple relationship types."""
    results = db.execute("""
        MATCH (a:Article {id: $id})-[:TAGGED]->(tag)<-[:TAGGED]-(related:Article)
        WHERE related <> a
        RETURN related, count(tag) as shared_tags
        ORDER BY shared_tags DESC
        LIMIT 5
    """, {'id': article_id})
    
    return results
```
