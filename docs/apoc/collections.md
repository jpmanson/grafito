# APOC: Collections, Maps, Text, Utilities

Grafito implements a small, useful subset of APOC functions for text, maps,
and collections. These functions can be used in any Cypher query.

## Text

### apoc.text.join

```cypher
RETURN apoc.text.join(['a', 'b', 'c'], '-') AS value
```

- Expects a list and a delimiter string.
- Returns `null` if any item in the list is `null`.

### apoc.text.split

```cypher
RETURN apoc.text.split('a,b,c', ',') AS parts
```

- Uses regex splitting.

### apoc.text.replace

```cypher
RETURN apoc.text.replace('a-b-c', '-', '_') AS value
```

- Uses regex replacement.

## Maps

### apoc.map.merge

```cypher
RETURN apoc.map.merge({a: 1}, {b: 2}) AS merged
```

### apoc.map.clean

```cypher
RETURN apoc.map.clean({a: 1, b: null, c: 'x'}, ['a'], [null]) AS cleaned
```

- Removes keys in `remove_keys` and values in `remove_values`.

### apoc.map.fromPairs

```cypher
RETURN apoc.map.fromPairs([['a', 1], ['b', 2]]) AS mapped
```

### apoc.map.removeKey

```cypher
RETURN apoc.map.removeKey({a: 1, b: 2}, 'a') AS updated
```

### apoc.map.get

```cypher
RETURN apoc.map.get({a: 1}, 'b', 0) AS value
```

## Convert

### apoc.convert.toMap

```cypher
RETURN apoc.convert.toMap([['a', 1], ['b', 2]]) AS mapped
```

- Accepts a map, list of pairs, or a node/relationship (uses its properties).

## Collections

### apoc.coll.contains

```cypher
RETURN apoc.coll.contains([1, 2, 3], 2) AS value
```

- Returns `null` if any element in the list is `null` and the target is not found.

### apoc.coll.toSet

```cypher
RETURN apoc.coll.toSet([1, 2, 2, 3]) AS value
```

- Returns unique values, preserving the original order.

## Utilities

### apoc.util.compress

```cypher
RETURN apoc.util.compress('hello', {compression: 'GZIP'}) AS bytes
```

Supported compressions: `DEFLATE`, `GZIP`, `BZ2`, `XZ`.
