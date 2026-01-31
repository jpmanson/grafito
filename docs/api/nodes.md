# Nodes API

Nodes are the primary entities in a property graph. This page covers all node-related operations.

## Creating Nodes

### Basic Node Creation

```python
from grafito import GrafitoDatabase

db = GrafitoDatabase(':memory:')

# Simple node with single label
alice = db.create_node(
    labels=['Person'],
    properties={'name': 'Alice', 'age': 30}
)

print(f"Created node with ID: {alice.id}")
print(f"Labels: {alice.labels}")  # ['Person']
print(f"Properties: {alice.properties}")  # {'name': 'Alice', 'age': 30}
```

### Multiple Labels

Nodes can have multiple labels, like implementing multiple interfaces:

```python
# Alice is a Person, an Employee, and a Manager
alice = db.create_node(
    labels=['Person', 'Employee', 'Manager'],
    properties={
        'name': 'Alice',
        'age': 30,
        'department': 'Engineering'
    }
)
```

Common patterns:
- `['User', 'Admin']` - Role-based permissions
- `['Product', 'Featured']` - Categorization
- `['Document', 'Published']` - Lifecycle states

### Property Types

Nodes support various property types:

```python
node = db.create_node(
    labels=['Document'],
    properties={
        # Basic types
        'title': 'Annual Report',
        'year': 2024,
        'rating': 4.5,
        'published': True,
        
        # Collections
        'tags': ['finance', 'annual', '2024'],
        'metadata': {
            'author': 'John Doe',
            'reviewers': ['Jane', 'Bob']
        },
        
        # Null values
        'archived_at': None
    }
)
```

## Retrieving Nodes

### Get by ID

```python
node = db.get_node(alice.id)

if node:
    print(f"Found: {node.properties['name']}")
    print(f"Labels: {node.labels}")
    print(f"Created at: {node.created_at}")
else:
    print("Node not found")
```

### Match Nodes

```python
# Match by labels
all_persons = db.match_nodes(labels=['Person'])

# Match by multiple labels (AND logic)
managers = db.match_nodes(labels=['Employee', 'Manager'])

# Match with property filter
engineers = db.match_nodes(
    labels=['Employee'],
    properties={'department': 'Engineering'}
)

# Iterate over results
for person in all_persons:
    print(f"{person.id}: {person.properties.get('name')}")
```

## Updating Nodes

### Update Properties

```python
# Partial update (merges with existing properties)
db.update_node_properties(alice.id, {
    'city': 'New York',
    'country': 'USA'
})

# Existing properties are preserved
# Now alice.properties includes: name, age, city, country
```

### Add Labels

```python
# Add new labels to existing node
db.add_labels(alice.id, ['Senior', 'TeamLead'])

# Labels are idempotent (adding existing label is a no-op)
db.add_labels(alice.id, ['Person'])  # Already exists, no error
```

### Remove Labels

```python
# Remove specific labels
db.remove_labels(alice.id, ['Manager'])

# Node keeps other labels
db.remove_labels(alice.id, ['TeamLead', 'Senior'])
```

## Deleting Nodes

```python
# Delete a node (also deletes all its relationships)
db.delete_node(node_id)

# Note: This is a permanent operation
# Use transactions for safety
with db:
    db.delete_node(node_id)
```

## Node Object

When you retrieve a node, you get a `Node` object with these attributes:

```python
node = db.get_node(node_id)

node.id              # Unique identifier (int)
node.labels          # List of labels (list[str])
node.properties      # Dictionary of properties (dict)
node.created_at      # Creation timestamp (datetime)
node.uri             # Optional URI identifier (str | None)
```

## Advanced Patterns

### Conditional Updates

```python
# Get and update in one transaction
with db:
    node = db.get_node(alice.id)
    if node and 'age' in node.properties:
        current_age = node.properties['age']
        db.update_node_properties(alice.id, {'age': current_age + 1})
```

### Bulk Operations

```python
# Create multiple nodes efficiently
with db:
    for i in range(100):
        db.create_node(
            labels=['User'],
            properties={'username': f'user_{i}', 'index': i}
        )
```

### Property Validation

```python
def create_validated_person(db, name, age):
    if not name or len(name) < 2:
        raise ValueError("Invalid name")
    if age < 0 or age > 150:
        raise ValueError("Invalid age")
    
    return db.create_node(
        labels=['Person'],
        properties={'name': name, 'age': age}
    )
```

## Common Workflows

### User Management

```python
def create_user(db, email, name):
    """Create a user with unique email constraint."""
    with db:
        # Check if email already exists
        existing = db.execute(
            "MATCH (n:User {email: $email}) RETURN n",
            {'email': email}
        )
        if existing:
            raise ValueError("Email already exists")
        
        return db.create_node(
            labels=['User'],
            properties={'email': email, 'name': name, 'active': True}
        )

def deactivate_user(db, user_id):
    """Soft-delete by marking inactive."""
    db.update_node_properties(user_id, {'active': False})
```

### Document Versioning

```python
def create_document_version(db, doc_id, content, version):
    """Create a new version of a document."""
    return db.create_node(
        labels=['Document', 'Version'],
        properties={
            'doc_id': doc_id,
            'content': content,
            'version': version,
            'created_at': datetime.now().isoformat()
        }
    )
```

## Best Practices

1. **Use Multiple Labels**: Leverage labels for categorization and querying
2. **Keep Properties Flat**: Avoid deeply nested structures when possible
3. **Use Transactions**: Wrap multiple operations for consistency
4. **Index Common Properties**: Create indexes on frequently queried properties
5. **Validate Input**: Check property values before creating/updating

## Error Handling

```python
from grafito.exceptions import NodeNotFoundError, ConstraintError

try:
    node = db.get_node(9999)  # Non-existent ID
    if node is None:
        print("Node not found")
        
    db.delete_node(9999)  # Will raise or handle gracefully
except NodeNotFoundError:
    print("Node does not exist")
except ConstraintError as e:
    print(f"Constraint violation: {e}")
```
