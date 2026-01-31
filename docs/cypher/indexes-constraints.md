# Indexes and Constraints

Schema management for performance and data integrity.

## Property Indexes

### Creating Node Indexes

**Programmatic API:**

```python
db.create_node_index('Person', 'name')
db.create_node_index('Person', 'email')  # Can index same label different props
```

**Cypher:**

```cypher
// Modern syntax
CREATE INDEX FOR (n:Person) ON (n.name)

// Alternative syntax
CREATE INDEX FOR NODE :Person(name)

// With explicit name
CREATE INDEX person_email_idx FOR (n:Person) ON (n.email)
```

### Creating Relationship Indexes

**Programmatic API:**

```python
db.create_relationship_index('KNOWS', 'since')
```

**Cypher:**

```cypher
// Modern syntax
CREATE INDEX FOR ()-[r:KNOWS]-() ON (r.since)

// Alternative syntax
CREATE INDEX FOR RELATIONSHIP :KNOWS(since)
```

### IF NOT EXISTS

```cypher
// Skip if already exists
CREATE INDEX IF NOT EXISTS FOR (n:Person) ON (n.name)
```

### Unique Indexes

```cypher
CREATE UNIQUE INDEX FOR (n:User) ON (n.email)
```

## URI Indexes

For URI/URL-based lookups:

```python
# Programmatic
db.create_node_uri_index()
db.create_relationship_uri_index()
```

```cypher
// Cypher
CALL db.uri_index.create('node')
CALL db.uri_index.create('relationship')
```

## Listing Indexes

```python
# Programmatic
indexes = db.list_indexes()
for idx in indexes:
    print(f"{idx['name']}: {idx['entity']}:{idx['label_or_type']}({idx['property']})")
```

```cypher
// All indexes
SHOW INDEXES

// Filtered
SHOW INDEXES WHERE entity = 'node'
SHOW INDEXES WHERE label_or_type = 'Person'
```

## Dropping Indexes

```python
db.drop_index('idx_node_person_name')
```

```cypher
// By name
DROP INDEX idx_node_person_name

// If exists
DROP INDEX IF EXISTS idx_node_person_name
```

## Constraints

### Uniqueness Constraints

```cypher
// Node property must be unique (nulls allowed)
CREATE CONSTRAINT FOR (n:User) REQUIRE n.email IS UNIQUE

// With name
CREATE CONSTRAINT user_email_unique FOR (n:User) REQUIRE n.email IS UNIQUE
```

### Existence Constraints

```cypher
// Property must exist on all nodes with label
CREATE CONSTRAINT FOR (n:Person) REQUIRE n.name IS NOT NULL
```

### Type Constraints

```cypher
// Property must be of specific type
CREATE CONSTRAINT FOR (n:Person) REQUIRE n.age IS INTEGER
CREATE CONSTRAINT FOR (n:User) REQUIRE n.active IS BOOLEAN
CREATE CONSTRAINT FOR (n:Product) REQUIRE n.price IS FLOAT
CREATE CONSTRAINT FOR (n:Document) REQUIRE n.tags IS LIST
CREATE CONSTRAINT FOR (n:Config) REQUIRE n.settings IS MAP
CREATE CONSTRAINT FOR (n:User) REQUIRE n.bio IS STRING
```

Supported types: `STRING`, `INTEGER`, `FLOAT`, `BOOLEAN`, `LIST`, `MAP`

### Relationship Constraints

```cypher
// All work relationships must have 'since' property
CREATE CONSTRAINT FOR ()-[r:WORKS_AT]-() REQUIRE r.since IS NOT NULL

// Type constraint on relationship property
CREATE CONSTRAINT FOR ()-[r:KNOWS]-() REQUIRE r.strength IS INTEGER
```

### Neo4j-Style Syntax

```cypher
// Alternative syntax for compatibility
CREATE CONSTRAINT FOR (n:Person) ON (n.email) IS UNIQUE
CREATE CONSTRAINT FOR (n:Person) ON (n.age) IS INTEGER
```

## Listing Constraints

```cypher
// All constraints
SHOW CONSTRAINTS

// Filtered
SHOW CONSTRAINTS WHERE entity = 'node'
SHOW CONSTRAINTS WHERE type = 'uniqueness'
```

## Dropping Constraints

```cypher
// By auto-generated name
DROP CONSTRAINT constraint_node_person_email_unique

// By custom name
DROP CONSTRAINT user_email_unique

// If exists
DROP CONSTRAINT IF EXISTS user_email_unique
```

## Constraint Behavior

### Uniqueness and NULL

```cypher
// NULL values are not checked for uniqueness
CREATE CONSTRAINT FOR (n:User) REQUIRE n.email IS UNIQUE

// These are both valid:
CREATE (u1:User {name: 'Alice'})  // email is null
CREATE (u2:User {name: 'Bob'})    // email is null (also null, allowed!)

// But this would fail:
CREATE (u3:User {email: 'a@b.com'})
CREATE (u4:User {email: 'a@b.com'})  // ERROR: duplicate
```

### Type Constraints Require Non-NULL

```cypher
CREATE CONSTRAINT FOR (n:Person) REQUIRE n.age IS INTEGER

// This fails - age is NULL
CREATE (p:Person {name: 'Alice'})

// This works
CREATE (p:Person {name: 'Alice', age: 30})

// This fails - wrong type
CREATE (p:Person {name: 'Bob', age: 'thirty'})
```

## Best Practices

### When to Create Indexes

```cypher
-- Index properties used in:
-- 1. MATCH lookups
CREATE INDEX FOR (n:User) ON (n.email)

-- 2. WHERE filters
CREATE INDEX FOR (n:Product) ON (n.category)

-- 3. ORDER BY
CREATE INDEX FOR (n:Post) ON (n.created_at)
```

### Index Strategy

```python
# Don't index everything - each index has overhead
# Index properties that are:
# - Frequently queried
# - High cardinality (many unique values)
# - Used for sorting

# Good candidates:
db.create_node_index('User', 'email')      # Unique lookup
db.create_node_index('Order', 'order_id')  # ID lookup

# Poor candidates:
# db.create_node_index('User', 'active')   # Low cardinality (true/false)
# db.create_node_index('Log', 'message')   # Never queried directly
```

### Constraints First

```cypher
-- Create constraints before importing data
-- Data with violations will be rejected

CREATE CONSTRAINT FOR (n:User) REQUIRE n.email IS UNIQUE;
CREATE CONSTRAINT FOR (n:User) REQUIRE n.name IS NOT NULL;

-- Now import data
CREATE (u:User {email: 'alice@example.com', name: 'Alice'});
```

## Troubleshooting

### Constraint Violation

```
ConstraintError: Node(123) already exists with label `User` and `email` = 'alice@example.com'
```

Solution: Use MERGE instead of CREATE for upsert semantics.

### Index Not Used

```cypher
-- Some queries can't use indexes
-- Pattern expressions in WHERE
WHERE (p)-[:KNOWS]->()  -- Can't use index on p

-- Functions on indexed property
WHERE toUpper(p.name) = 'ALICE'  -- Won't use index

-- Instead, normalize on insert:
SET p.name_lower = toLower(p.name)
-- Then query:
WHERE p.name_lower = 'alice'
```
