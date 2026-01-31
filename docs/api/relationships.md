# Relationships API

Relationships connect nodes and represent how entities relate to each other.

## Creating Relationships

### Basic Relationship

```python
# Create a directed relationship from Alice to Bob
knows = db.create_relationship(
    source_id=alice.id,    # From
    target_id=bob.id,      # To
    rel_type='KNOWS'       # Relationship type
)

print(f"Created relationship: {knows.id}")
print(f"Type: {knows.type}")  # 'KNOWS'
print(f"From: {knows.source_id} -> To: {knows.target_id}")
```

### Relationship with Properties

```python
# Relationships can have properties just like nodes
works_at = db.create_relationship(
    source_id=alice.id,
    target_id=company.id,
    rel_type='WORKS_AT',
    properties={
        'since': 2020,
        'position': 'Senior Engineer',
        'department': 'Engineering',
        'salary_band': 'L5'
    }
)
```

### Common Relationship Types

| Type | Description | Example Properties |
|------|-------------|-------------------|
| `KNOWS` | Social connection | `since`, `strength` |
| `WORKS_AT` | Employment | `since`, `position`, `department` |
| `MANAGES` | Management | `since`, `level` |
| `CREATED` | Authorship | `date`, `role` |
| `BELONGS_TO` | Categorization | `priority`, `weight` |
| `LOCATED_IN` | Geography | `address_type` |

## Retrieving Relationships

### Get by ID

```python
rel = db.get_relationship(rel_id)

if rel:
    print(f"Type: {rel.type}")
    print(f"Properties: {rel.properties}")
    print(f"Created: {rel.created_at}")
```

### Match Relationships

```python
# Find all relationships of a type
all_knows = db.match_relationships(rel_type='KNOWS')

# Find relationships from a specific node
from_alice = db.match_relationships(source_id=alice.id)

# Find relationships to a specific node
to_bob = db.match_relationships(target_id=bob.id)

# Combine filters
alice_to_bob = db.match_relationships(
    source_id=alice.id,
    target_id=bob.id,
    rel_type='KNOWS'
)
```

### Get Neighbors

The most common pattern is getting connected nodes:

```python
# Get all outgoing connections
friends = db.get_neighbors(
    node_id=alice.id,
    direction='outgoing',
    rel_type='KNOWS'
)

# Get all incoming connections (who knows Alice?)
followers = db.get_neighbors(
    node_id=alice.id,
    direction='incoming',
    rel_type='KNOWS'
)

# Get connections in both directions
all_connected = db.get_neighbors(
    node_id=alice.id,
    direction='both'
)

# Get all neighbors regardless of relationship type
all_neighbors = db.get_neighbors(alice.id, direction='outgoing')
```

## Deleting Relationships

```python
# Delete a specific relationship
db.delete_relationship(rel_id)

# Note: Deleting a node automatically deletes all its relationships
```

## Relationship Object

```python
rel = db.get_relationship(rel_id)

rel.id              # Unique identifier (int)
rel.type            # Relationship type (str)
rel.source_id       # Source node ID (int)
rel.target_id       # Target node ID (int)
rel.properties      # Dictionary of properties (dict)
rel.created_at      # Creation timestamp (datetime)
rel.uri             # Optional URI identifier (str | None)
```

## Direction Matters

Relationships are directed. Remember the arrow direction:

```python
# Alice WORKS_AT Company (correct direction)
db.create_relationship(alice.id, company.id, 'WORKS_AT')

# This is different! Company WORKS_AT Alice
db.create_relationship(company.id, alice.id, 'WORKS_AT')

# For bidirectional relationships, create two
db.create_relationship(alice.id, bob.id, 'KNOWS')
db.create_relationship(bob.id, alice.id, 'KNOWS')  # Mutual
```

## Advanced Patterns

### Creating Linked Structures

```python
def create_reporting_chain(db, manager, employees):
    """Create MANAGES relationships from manager to employees."""
    with db:
        for emp in employees:
            db.create_relationship(
                source_id=manager.id,
                target_id=emp.id,
                rel_type='MANAGES',
                properties={'since': datetime.now().year}
            )
```

### Updating Relationship Properties

Currently, relationships are updated via Cypher:

```python
# Update relationship properties
db.execute("""
    MATCH (a:Person {name: 'Alice'})-[r:WORKS_AT]->(c:Company)
    SET r.position = 'Staff Engineer'
""")
```

### Finding Relationship Paths

```python
# Find all paths between two nodes with specific relationship
results = db.execute("""
    MATCH path = (a:Person {name: 'Alice'})-[:KNOWS*1..3]->(b:Person {name: 'Carol'})
    RETURN path
""")
```

## Best Practices

1. **Use Verbose Type Names**: `WORKS_AT` is clearer than `WORKS`
2. **Consider Direction**: Always think about the natural direction
3. **Keep Properties Lean**: Don't duplicate node data in relationships
4. **Use Transactions**: For consistency when creating node + relationship

## Common Workflows

### Social Network

```python
def make_friends(db, person1_id, person2_id):
    """Create bidirectional friendship."""
    with db:
        timestamp = datetime.now().isoformat()
        
        db.create_relationship(
            person1_id, person2_id, 'FRIEND',
            properties={'since': timestamp, 'strength': 'strong'}
        )
        db.create_relationship(
            person2_id, person1_id, 'FRIEND',
            properties={'since': timestamp, 'strength': 'strong'}
        )
```

### Content Graph

```python
def link_content(db, article_id, tag_ids):
    """Link an article to multiple tags."""
    with db:
        for tag_id in tag_ids:
            db.create_relationship(
                article_id, tag_id, 'TAGGED_WITH',
                properties={'auto': False}
            )
```

### Organization Hierarchy

```python
def create_department_structure(db, dept_data):
    """Create department with manager and employees."""
    with db:
        dept = db.create_node(
            labels=['Department'],
            properties={'name': dept_data['name']}
        )
        
        # Link manager
        db.create_relationship(
            dept_data['manager_id'], dept.id, 'MANAGES_DEPT'
        )
        
        # Link employees
        for emp_id in dept_data['employee_ids']:
            db.create_relationship(
                emp_id, dept.id, 'BELONGS_TO',
                properties={'type': 'member'}
            )
        
        return dept
```

## Error Handling

```python
from grafito.exceptions import RelationshipError, NodeNotFoundError

try:
    rel = db.create_relationship(
        source_id=9999,  # Non-existent node
        target_id=bob.id,
        rel_type='KNOWS'
    )
except NodeNotFoundError:
    print("One or both nodes don't exist")
except RelationshipError as e:
    print(f"Relationship error: {e}")
```
