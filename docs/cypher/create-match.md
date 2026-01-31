# CREATE and MATCH

The two most fundamental Cypher operations: creating data and finding data.

## CREATE

Creates nodes and relationships.

### Create Nodes

```cypher
// Simple node
CREATE (n)

// With label
CREATE (p:Person)

// With multiple labels
CREATE (p:Person:Employee)

// With properties
CREATE (p:Person {name: 'Alice', age: 30})

// With complex properties
CREATE (p:Person {
    name: 'Bob',
    tags: ['developer', 'python'],
    metadata: {joined: '2024-01-15'}
})
```

### Create Relationships

```cypher
// Create both nodes and relationship
CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})

// Create relationship between existing nodes
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
CREATE (a)-[:KNOWS {since: 2020}]->(b)

// Create multiple relationships
CREATE (a)-[:KNOWS]->(b)-[:KNOWS]->(c)
```

### Create Multiple Elements

```cypher
// Separate with commas
CREATE
  (a:Person {name: 'Alice'}),
  (b:Person {name: 'Bob'}),
  (c:Company {name: 'TechCorp'}),
  (a)-[:KNOWS]->(b),
  (a)-[:WORKS_AT]->(c)
```

### Create and Return

```cypher
CREATE (p:Person {name: 'Alice'})
RETURN p
```

## MATCH

Finds existing patterns in the graph.

### Match Nodes

```cypher
// Any node
MATCH (n)
RETURN n

// By label
MATCH (p:Person)
RETURN p

// By multiple labels
MATCH (p:Person:Employee)
RETURN p

// By property
MATCH (p:Person {name: 'Alice'})
RETURN p

// By multiple properties
MATCH (p:Person {name: 'Alice', age: 30})
RETURN p
```

### Match Relationships

```cypher
// Any relationship
MATCH ()-[r]->()
RETURN r

// By type
MATCH ()-[r:KNOWS]->()
RETURN r

// With direction
MATCH (a)-[r:KNOWS]->(b)
RETURN a.name, b.name

// Both directions
MATCH (a)-[r:KNOWS]-(b)
RETURN a.name, b.name

// Specific nodes
MATCH (a:Person)-[r:KNOWS]->(b:Person)
RETURN a.name, b.name
```

### Match with Properties

```cypher
// Properties in pattern
MATCH (p:Person {name: 'Alice'})-[:KNOWS]->(friend)
RETURN friend.name

// Properties on relationship
MATCH (a)-[r:WORKS_AT {since: 2020}]->(b)
RETURN a.name, b.name
```

## Combining CREATE and MATCH

### Connect Existing Nodes

```python
# First create nodes
db.execute("""
    CREATE (a:Person {name: 'Alice'}),
           (b:Person {name: 'Bob'})
""")

# Then connect them
db.execute("""
    MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
    CREATE (a)-[:KNOWS {since: 2020}]->(b)
""")
```

### Find or Create Pattern

Use `MERGE` for find-or-create (see [Data Modification](modification.md)):

```cypher
MERGE (p:Person {email: 'alice@example.com'})
ON CREATE SET p.name = 'Alice', p.created = datetime()
ON MATCH SET p.lastSeen = datetime()
RETURN p
```

## Variable-Length Matching

### Fixed Length

```cypher
// Exactly 2 hops (friends of friends)
MATCH (a:Person {name: 'Alice'})-[:KNOWS*2]->(fof)
RETURN fof
```

### Range

```cypher
// 1 to 3 hops
MATCH (a:Person {name: 'Alice'})-[:KNOWS*1..3]->(other)
RETURN other
```

### Unbounded

Uses default max hops configured at database creation:

```python
db = GrafitoDatabase(':memory:', cypher_max_hops=5)
```

```cypher
// Uses default max hops
MATCH (a:Person)-[:KNOWS*..]->(other)
RETURN other
```

## Shortest Path

```cypher
// Single shortest path
MATCH p = shortestPath(
  (a:Person {name: 'Alice'})-[:KNOWS*1..5]->(b:Person {name: 'Bob'})
)
RETURN p, length(p) as hops

// All shortest paths
MATCH p = allShortestPaths(
  (a:Person {name: 'Alice'})-[:KNOWS*1..5]->(b:Person {name: 'Bob'})
)
RETURN p
```

## Pattern Comprehensions

Collect related nodes in a list:

```cypher
// Get Alice's friends as a list
MATCH (a:Person {name: 'Alice'})
RETURN [(a)-[:KNOWS]->(b) | b.name] as friends

// With filter
MATCH (a:Person {name: 'Alice'})
RETURN [(a)-[:KNOWS]->(b) WHERE b.active | b.name] as activeFriends
```

## Common Patterns

### Social Network

```cypher
// Friends of friends
MATCH (me:Person {name: 'Alice'})-[:KNOWS]->()-[:KNOWS]->(fof)
WHERE fof <> me
RETURN DISTINCT fof.name
```

### Organization Hierarchy

```cypher
// All reports to a manager
MATCH (mgr:Person {name: 'Alice'})<-[:REPORTS_TO*]-(emp)
RETURN emp.name
```

### Recommendation

```cypher
// People with similar interests
MATCH (me:Person)-[:INTERESTED_IN]->(interest)<-[:INTERESTED_IN]-(other)
WHERE me.name = 'Alice' AND other <> me
RETURN other.name, count(interest) as common
ORDER BY common DESC
```
