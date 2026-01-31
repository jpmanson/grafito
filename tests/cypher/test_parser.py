"""Tests for the Cypher parser."""

import pytest
from grafito.cypher.lexer import Lexer
from grafito.cypher.parser import Parser
from grafito.cypher.ast_nodes import (
    Query, CreateClause, MatchClause, WhereClause, ReturnClause, WithClause,
    NodePattern, RelationshipPattern, Pattern, PatternElement,
    ReturnItem, PropertyAccess, Literal, BinaryOp, UnaryOp, CaseExpression, Variable,
    PatternComprehension, UnwindClause, PatternFunction, FunctionCallExpression,
    CreateIndexClause, DropIndexClause, ShowIndexesClause,
    CreateConstraintClause, DropConstraintClause, ShowConstraintsClause,
    ForeachClause, SetClause, ListLiteral, MapLiteral
)
from grafito.cypher.exceptions import CypherSyntaxError


def parse_query(query: str) -> Query:
    """Helper to tokenize and parse a query."""
    lexer = Lexer(query)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def literalize(expr):
    if isinstance(expr, Literal):
        return expr.value
    if isinstance(expr, ListLiteral):
        return [literalize(item) for item in expr.items]
    if isinstance(expr, MapLiteral):
        return {key: literalize(value) for key, value in expr.items.items()}
    raise AssertionError(f"Unexpected expression type: {type(expr)}")


class TestParserCreate:
    """Test parsing CREATE clauses."""

    def test_parse_create_simple_node(self):
        query = parse_query("CREATE (n)")
        assert isinstance(query.clause, CreateClause)
        assert len(query.clause.patterns) == 1
        pattern = query.clause.patterns[0]
        assert len(pattern.elements) == 1
        node = pattern.elements[0].node
        assert node.variable == "n"
        assert node.labels == []
        assert node.properties == {}

    def test_parse_create_node_with_label(self):
        query = parse_query("CREATE (n:Person)")
        node = query.clause.patterns[0].elements[0].node
        assert node.variable == "n"
        assert node.labels == ["Person"]
        assert node.properties == {}

    def test_parse_create_node_with_multiple_labels(self):
        query = parse_query("CREATE (n:Person:Employee)")
        node = query.clause.patterns[0].elements[0].node
        assert node.variable == "n"
        assert node.labels == ["Person", "Employee"]
        assert node.properties == {}

    def test_parse_create_anonymous_node(self):
        query = parse_query("CREATE (:Person)")
        node = query.clause.patterns[0].elements[0].node
        assert node.variable is None
        assert node.labels == ["Person"]

    def test_parse_create_node_with_string_property(self):
        query = parse_query("CREATE (n:Person {name: 'Alice'})")
        node = query.clause.patterns[0].elements[0].node
        assert node.variable == "n"
        assert node.labels == ["Person"]
        assert {key: literalize(value) for key, value in node.properties.items()} == {"name": "Alice"}

    def test_parse_create_node_with_integer_property(self):
        query = parse_query("CREATE (n:Person {age: 30})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {"age": 30}

    def test_parse_create_node_with_float_property(self):
        query = parse_query("CREATE (n:Person {score: 98.5})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {"score": 98.5}

    def test_parse_create_node_with_boolean_property(self):
        query = parse_query("CREATE (n:Person {active: true})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {"active": True}

    def test_parse_create_node_with_null_property(self):
        query = parse_query("CREATE (n:Person {middle_name: null})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {"middle_name": None}

    def test_parse_create_node_with_multiple_properties(self):
        query = parse_query("CREATE (n:Person {name: 'Alice', age: 30, active: true})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {
            "name": "Alice",
            "age": 30,
            "active": True,
        }

    def test_parse_create_node_with_list_property(self):
        query = parse_query("CREATE (n:Person {tags: ['a', 'b']})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {"tags": ["a", "b"]}

    def test_parse_create_node_with_map_property(self):
        query = parse_query("CREATE (n:Person {meta: {score: 1}})")
        node = query.clause.patterns[0].elements[0].node
        assert {key: literalize(value) for key, value in node.properties.items()} == {"meta": {"score": 1}}


class TestParserMatch:
    """Test parsing MATCH clauses."""

    def test_parse_match_simple_node(self):
        query = parse_query("MATCH (n)")
        assert isinstance(query.clause, MatchClause)
        assert len(query.clause.patterns) == 1
        node = query.clause.patterns[0].elements[0].node
        assert node.variable == "n"
        assert node.labels == []

    def test_parse_match_node_with_label(self):
        query = parse_query("MATCH (n:Person)")
        node = query.clause.patterns[0].elements[0].node
        assert node.variable == "n"
        assert node.labels == ["Person"]

    def test_parse_match_node_with_properties(self):
        query = parse_query("MATCH (n:Person {name: 'Alice'})")
        node = query.clause.patterns[0].elements[0].node
        assert node.labels == ["Person"]
        assert {key: literalize(value) for key, value in node.properties.items()} == {"name": "Alice"}


class TestParserRelationshipPattern:
    """Test parsing relationship patterns."""

    def test_parse_outgoing_relationship(self):
        query = parse_query("MATCH (a)-[r:KNOWS]->(b)")
        pattern = query.clause.patterns[0]
        assert len(pattern.elements) == 2

        # First element: (a) with relationship
        elem1 = pattern.elements[0]
        assert elem1.node.variable == "a"
        assert elem1.relationship is not None
        assert elem1.relationship.variable == "r"
        assert elem1.relationship.rel_type == "KNOWS"
        assert elem1.relationship.direction == "outgoing"

        # Second element: (b)
        elem2 = pattern.elements[1]
        assert elem2.node.variable == "b"

    def test_parse_incoming_relationship(self):
        query = parse_query("MATCH (a)<-[r:KNOWS]-(b)")
        pattern = query.clause.patterns[0]
        elem1 = pattern.elements[0]
        assert elem1.relationship.direction == "incoming"

    def test_parse_bidirectional_relationship(self):
        query = parse_query("MATCH (a)-[r:KNOWS]-(b)")
        pattern = query.clause.patterns[0]
        elem1 = pattern.elements[0]
        assert elem1.relationship.direction == "both"

    def test_parse_anonymous_relationship(self):
        query = parse_query("MATCH (a)-[:KNOWS]->(b)")
        pattern = query.clause.patterns[0]
        elem1 = pattern.elements[0]
        assert elem1.relationship.variable is None
        assert elem1.relationship.rel_type == "KNOWS"

    def test_parse_relationship_with_properties(self):
        query = parse_query("MATCH (a)-[r:KNOWS {since: 2020}]->(b)")
        pattern = query.clause.patterns[0]
        elem1 = pattern.elements[0]
        assert {key: literalize(value) for key, value in elem1.relationship.properties.items()} == {"since": 2020}

    def test_parse_relationship_variable_length_range(self):
        query = parse_query("MATCH (a)-[:KNOWS*1..3]->(b)")
        pattern = query.clause.patterns[0]
        rel = pattern.elements[0].relationship
        assert rel.min_hops == 1
        assert rel.max_hops == 3

    def test_parse_relationship_variable_length_single(self):
        query = parse_query("MATCH (a)-[:KNOWS*2]->(b)")
        pattern = query.clause.patterns[0]
        rel = pattern.elements[0].relationship
        assert rel.min_hops == 2
        assert rel.max_hops == 2

    def test_parse_relationship_variable_length_unbounded(self):
        query = parse_query("MATCH (a)-[:KNOWS*..]->(b)")
        pattern = query.clause.patterns[0]
        rel = pattern.elements[0].relationship
        assert rel.min_hops == 1
        assert rel.max_hops is None

    def test_parse_multi_hop_variable_length_relationships(self):
        query = parse_query(
            "MATCH (a)-[r1:KNOWS*1..2]->(b)-[r2:WORKS_AT]->(c) RETURN r1, r2"
        )
        pattern = query.clause.patterns[0]
        rel1 = pattern.elements[0].relationship
        rel2 = pattern.elements[1].relationship
        assert rel1.variable == "r1"
        assert rel1.min_hops == 1
        assert rel1.max_hops == 2
        assert rel2.variable == "r2"

    def test_parse_relationship_with_node_labels(self):
        query = parse_query("MATCH (a:Person)-[r:KNOWS]->(b:Person)")
        pattern = query.clause.patterns[0]
        assert pattern.elements[0].node.labels == ["Person"]
        assert pattern.elements[1].node.labels == ["Person"]


class TestParserWhereClause:
    """Test parsing WHERE clauses."""

    def test_parse_where_simple_comparison(self):
        query = parse_query("MATCH (n:Person) WHERE n.age > 25")
        where = query.clause.where_clause
        assert where is not None
        assert isinstance(where.condition, BinaryOp)
        assert where.condition.operator == ">"
        assert isinstance(where.condition.left, PropertyAccess)
        assert where.condition.left.variable == "n"
        assert where.condition.left.property == "age"


class TestParserFunctionCalls:
    """Test parsing of function calls."""

    def test_parse_apoc_function_call(self):
        query = parse_query("WITH 1 AS dummy RETURN apoc.text.join(['a','b'], ',') AS joined")
        assert isinstance(query.clause, WithClause)
        assert isinstance(query.clause.return_clause, ReturnClause)
        item = query.clause.return_clause.items[0]
        assert isinstance(item, ReturnItem)
        assert isinstance(item.expression, FunctionCallExpression)
        assert item.expression.name == "apoc.text.join"


class TestParserIndexClauses:
    """Test parsing of index clauses."""

    def test_parse_create_node_index(self):
        query = parse_query("CREATE INDEX FOR NODE :Person(name)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "node"
        assert query.clause.label_or_type == "Person"
        assert query.clause.property == "name"

    def test_parse_create_index_legacy(self):
        query = parse_query("CREATE INDEX ON :Person(name)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "node"
        assert query.clause.label_or_type == "Person"
        assert query.clause.property == "name"

    def test_parse_create_relationship_index(self):
        query = parse_query("CREATE INDEX FOR RELATIONSHIP :KNOWS(since)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.property == "since"

    def test_parse_create_index_named(self):
        query = parse_query("CREATE INDEX idx_person_name FOR NODE :Person(name)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.name == "idx_person_name"

    def test_parse_create_index_if_not_exists(self):
        query = parse_query("CREATE INDEX IF NOT EXISTS FOR NODE :Person(name)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.if_not_exists is True
        assert query.clause.unique is False

    def test_parse_create_unique_index(self):
        query = parse_query("CREATE UNIQUE INDEX FOR NODE :Person(email)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.unique is True

    def test_parse_create_unique_index_if_not_exists(self):
        query = parse_query("CREATE UNIQUE INDEX IF NOT EXISTS FOR NODE :Person(email)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.unique is True
        assert query.clause.if_not_exists is True

    def test_parse_drop_index(self):
        query = parse_query("DROP INDEX idx_person_name")
        assert isinstance(query.clause, DropIndexClause)
        assert query.clause.name == "idx_person_name"

    def test_parse_drop_index_if_exists(self):
        query = parse_query("DROP INDEX IF EXISTS idx_person_name")
        assert isinstance(query.clause, DropIndexClause)
        assert query.clause.if_exists is True

    def test_parse_show_indexes(self):
        query = parse_query("SHOW INDEXES")
        assert isinstance(query.clause, ShowIndexesClause)

    def test_parse_show_indexes_where(self):
        query = parse_query("SHOW INDEXES WHERE entity = 'node'")
        assert isinstance(query.clause, ShowIndexesClause)
        assert query.clause.where_expr is not None

    def test_parse_create_index_neo4j_node(self):
        query = parse_query("CREATE INDEX FOR (n:Person) ON (n.name)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "node"
        assert query.clause.label_or_type == "Person"
        assert query.clause.property == "name"

    def test_parse_create_index_neo4j_node_without_var(self):
        query = parse_query("CREATE INDEX FOR (:Person) ON (n.name)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "node"
        assert query.clause.label_or_type == "Person"
        assert query.clause.property == "name"

    def test_parse_create_index_neo4j_relationship(self):
        query = parse_query("CREATE INDEX FOR ()-[r:KNOWS]-() ON (r.since)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.property == "since"

    def test_parse_create_index_neo4j_relationship_without_var(self):
        query = parse_query("CREATE INDEX FOR ()-[:KNOWS]-() ON (r.since)")
        assert isinstance(query.clause, CreateIndexClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.property == "since"


class TestParserConstraintClauses:
    """Test parsing of constraint clauses."""

    def test_parse_create_unique_constraint(self):
        query = parse_query("CREATE CONSTRAINT FOR NODE :Person REQUIRE email IS UNIQUE")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.constraint_type == "UNIQUE"

    def test_parse_create_exists_constraint(self):
        query = parse_query("CREATE CONSTRAINT FOR NODE :Person REQUIRE name IS NOT NULL")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.constraint_type == "EXISTS"

    def test_parse_create_type_constraint(self):
        query = parse_query("CREATE CONSTRAINT FOR NODE :Person REQUIRE age IS INTEGER")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.constraint_type == "TYPE"
        assert query.clause.type_name == "INTEGER"

    def test_parse_create_constraint_if_not_exists(self):
        query = parse_query("CREATE CONSTRAINT IF NOT EXISTS FOR NODE :Person REQUIRE email IS UNIQUE")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.if_not_exists is True

    def test_parse_create_constraint_named(self):
        query = parse_query("CREATE CONSTRAINT person_email_unique FOR NODE :Person REQUIRE email IS UNIQUE")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.name == "person_email_unique"

    def test_parse_drop_constraint(self):
        query = parse_query("DROP CONSTRAINT person_email_unique")
        assert isinstance(query.clause, DropConstraintClause)
        assert query.clause.name == "person_email_unique"

    def test_parse_drop_constraint_if_exists(self):
        query = parse_query("DROP CONSTRAINT IF EXISTS person_email_unique")
        assert isinstance(query.clause, DropConstraintClause)
        assert query.clause.if_exists is True

    def test_parse_show_constraints(self):
        query = parse_query("SHOW CONSTRAINTS WHERE entity = 'node'")
        assert isinstance(query.clause, ShowConstraintsClause)

    def test_parse_create_constraint_neo4j_relationship_unique(self):
        query = parse_query("CREATE CONSTRAINT FOR ()-[r:KNOWS]-() REQUIRE r.since IS UNIQUE")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.constraint_type == "UNIQUE"

    def test_parse_create_constraint_neo4j_relationship_exists(self):
        query = parse_query("CREATE CONSTRAINT FOR ()-[r:KNOWS]-() REQUIRE r.since IS NOT NULL")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.constraint_type == "EXISTS"

    def test_parse_create_constraint_neo4j_relationship_type(self):
        query = parse_query("CREATE CONSTRAINT FOR ()-[r:KNOWS]-() REQUIRE r.since IS INTEGER")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.constraint_type == "TYPE"

    def test_parse_create_constraint_on_style(self):
        query = parse_query("CREATE CONSTRAINT FOR (n:Person) ON (n.email) IS UNIQUE")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.constraint_type == "UNIQUE"

    def test_parse_create_constraint_on_style_relationship(self):
        query = parse_query("CREATE CONSTRAINT FOR ()-[r:KNOWS]-() ON (r.since) IS INTEGER")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.entity == "relationship"
        assert query.clause.label_or_type == "KNOWS"
        assert query.clause.constraint_type == "TYPE"

    def test_parse_create_constraint_legacy(self):
        query = parse_query("CREATE CONSTRAINT ON (p:Person) ASSERT p.id IS UNIQUE")
        assert isinstance(query.clause, CreateConstraintClause)
        assert query.clause.entity == "node"
        assert query.clause.label_or_type == "Person"
        assert query.clause.property == "id"
        assert query.clause.constraint_type == "UNIQUE"


class TestParserForeach:
    """Test parsing of FOREACH."""

    def test_parse_foreach_set(self):
        query = parse_query("FOREACH (x IN [1,2] | SET n.age = x)")
        assert isinstance(query.clause, ForeachClause)
        assert query.clause.variable == "x"
        assert isinstance(query.clause.actions[0], SetClause)

    def test_parse_foreach_merge(self):
        query = parse_query("FOREACH (x IN [1,2] | MERGE (n {id: x}))")
        assert isinstance(query.clause, ForeachClause)
        assert query.clause.variable == "x"

    def test_parse_where_equality(self):
        query = parse_query("MATCH (n) WHERE n.name = 'Alice'")
        where = query.clause.where_clause
        assert where.condition.operator == "="
        assert where.condition.right.value == "Alice"

    def test_parse_where_inequality(self):
        query = parse_query("MATCH (n) WHERE n.name != 'Bob'")
        where = query.clause.where_clause
        assert where.condition.operator == "!="

    def test_parse_where_in(self):
        query = parse_query("MATCH (n) WHERE n.age IN [20, 30]")
        where = query.clause.where_clause
        assert where.condition.operator == "IN"

    def test_parse_where_any(self):
        query = parse_query("MATCH (n) WHERE ANY(x IN [1,2,3] WHERE x > 2) RETURN n")
        where = query.clause.where_clause
        assert where is not None
    
    def test_parse_where_any_without_where(self):
        query = parse_query("MATCH (n) WHERE ANY(x IN [true, false]) RETURN n")
        where = query.clause.where_clause
        assert where is not None

    def test_parse_where_any_relationship_property(self):
        query = parse_query(
            "MATCH (a)-[r:KNOWS*1..2]->(b) "
            "WHERE ANY(rel IN r WHERE rel.since > 2020) RETURN b"
        )
        where = query.clause.where_clause
        assert where is not None

    def test_parse_where_all_relationship_property(self):
        query = parse_query(
            "MATCH (a)-[r:KNOWS*1..2]->(b) "
            "WHERE ALL(rel IN r WHERE rel.since > 2020) RETURN b"
        )
        where = query.clause.where_clause
        assert where is not None

    def test_parse_where_none_relationship_property(self):
        query = parse_query(
            "MATCH (a)-[r:KNOWS*1..2]->(b) "
            "WHERE NONE(rel IN r WHERE rel.since > 2020) RETURN b"
        )
        where = query.clause.where_clause
        assert where is not None

    def test_parse_where_single_relationship_property(self):
        query = parse_query(
            "MATCH (a)-[r:KNOWS*1..2]->(b) "
            "WHERE SINGLE(rel IN r WHERE rel.since > 2020) RETURN b"
        )
        where = query.clause.where_clause
        assert where is not None

    def test_parse_where_and(self):
        query = parse_query("MATCH (n) WHERE n.age > 25 AND n.city = 'NYC'")
        where = query.clause.where_clause
        assert isinstance(where.condition, BinaryOp)
        assert where.condition.operator == "AND"
        assert isinstance(where.condition.left, BinaryOp)  # n.age > 25
        assert isinstance(where.condition.right, BinaryOp)  # n.city = 'NYC'

    def test_parse_where_or(self):
        query = parse_query("MATCH (n) WHERE n.age > 30 OR n.city = 'LA'")
        where = query.clause.where_clause
        assert where.condition.operator == "OR"

    def test_parse_where_not(self):
        query = parse_query("MATCH (n) WHERE NOT n.active")
        where = query.clause.where_clause
        assert isinstance(where.condition, UnaryOp)
        assert where.condition.operator == "NOT"

    def test_parse_where_is_null(self):
        query = parse_query("MATCH (n) WHERE n.age IS NULL")
        where = query.clause.where_clause
        assert isinstance(where.condition, UnaryOp)
        assert where.condition.operator == "IS NULL"

    def test_parse_where_is_not_null(self):
        query = parse_query("MATCH (n) WHERE n.age IS NOT NULL")
        where = query.clause.where_clause
        assert isinstance(where.condition, UnaryOp)
        assert where.condition.operator == "IS NOT NULL"

    def test_parse_where_complex(self):
        query = parse_query("MATCH (n) WHERE n.age > 25 AND (n.city = 'NYC' OR n.city = 'LA')")
        where = query.clause.where_clause
        # Top level: AND
        assert where.condition.operator == "AND"
        # Right side should be OR
        assert isinstance(where.condition.right, BinaryOp)
        assert where.condition.right.operator == "OR"


class TestParserReturnClause:
    """Test parsing RETURN clauses."""

    def test_parse_return_variable(self):
        query = parse_query("MATCH (n) RETURN n")
        ret = query.clause.return_clause
        assert ret is not None
        assert len(ret.items) == 1
        assert isinstance(ret.items[0].expression, Variable)
        assert ret.items[0].expression.name == "n"

    def test_parse_return_property(self):
        query = parse_query("MATCH (n) RETURN n.name")
        ret = query.clause.return_clause
        assert len(ret.items) == 1
        assert isinstance(ret.items[0].expression, PropertyAccess)
        assert ret.items[0].expression.variable == "n"
        assert ret.items[0].expression.property == "name"

    def test_parse_return_multiple(self):
        query = parse_query("MATCH (n) RETURN n.name, n.age")
        ret = query.clause.return_clause
        assert len(ret.items) == 2
        assert ret.items[0].expression.property == "name"
        assert ret.items[1].expression.property == "age"

    def test_parse_return_mixed(self):
        query = parse_query("MATCH (n) RETURN n, n.name")
        ret = query.clause.return_clause
        assert len(ret.items) == 2

    def test_parse_return_list_literal(self):
        query = parse_query("MATCH (n) RETURN [1, 2, 3]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_list_literal_with_negative(self):
        query = parse_query("MATCH (n) RETURN [-1, 2]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_list_literal_with_exponent(self):
        query = parse_query("MATCH (n) RETURN [1e-3, -2.5e2]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_list_comprehension(self):
        query = parse_query("MATCH (n) RETURN [x IN [1,2,3] WHERE x > 1 | x]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1
    
    def test_parse_return_list_comprehension_property_access(self):
        query = parse_query("MATCH (n) RETURN [x IN [n] WHERE x.age > 1 | x.name]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_list_comprehension_relationship_property(self):
        query = parse_query("MATCH (a)-[r]->(b) RETURN [rel IN [r] WHERE rel.since > 0 | rel.since]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_pattern_comprehension(self):
        query = parse_query(
            "MATCH (n) RETURN [(n)-[:KNOWS]->(m) WHERE m.age > 20 | m.name]"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 1
        assert isinstance(ret.items[0].expression, PatternComprehension)

    def test_parse_return_pattern_comprehension_multi_hop(self):
        query = parse_query(
            "MATCH (n) RETURN [(n)-[:KNOWS]->(m)-[:WORKS_AT]->(c) WHERE c.name = 'Acme' | m.name]"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 1
        assert isinstance(ret.items[0].expression, PatternComprehension)

    def test_parse_return_list_index(self):
        query = parse_query("MATCH (n) RETURN [1,2,3][1]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_list_functions(self):
        query = parse_query("MATCH (n) RETURN size([1,2]), range(1,3)")
        ret = query.clause.return_clause
        assert len(ret.items) == 2

    def test_parse_return_distinct(self):
        query = parse_query("MATCH (n) RETURN DISTINCT n.name")
        ret = query.clause.return_clause
        assert ret.distinct is True

    def test_parse_with_distinct(self):
        query = parse_query("MATCH (n) WITH DISTINCT n RETURN n")
        with_clause = query.clauses[1]
        assert with_clause.distinct is True

    def test_parse_return_collect(self):
        query = parse_query("MATCH (n) RETURN COLLECT(n)")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_count_distinct(self):
        query = parse_query("MATCH (n) RETURN COUNT(DISTINCT n)")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_stddev_percentilecont(self):
        query = parse_query("MATCH (n) RETURN stdDev(n.score), percentileCont(n.score, 0.5)")
        ret = query.clause.return_clause
        assert len(ret.items) == 2

    def test_parse_return_point_distance(self):
        query = parse_query("MATCH (n) RETURN point({x: 0, y: 3}), distance(point({x: 0, y: 3}), point({x: 0, y: 0}))")
        ret = query.clause.return_clause
        assert len(ret.items) == 2

    def test_parse_return_temporal_truncate_between(self):
        query = parse_query(
            "MATCH (n) RETURN date.truncate('month', date('2024-02-20')), "
            "duration.between(date('2024-01-01'), date('2024-01-03'))"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 2

    def test_parse_return_list_slice(self):
        query = parse_query("MATCH (n) RETURN [1,2,3,4][1..3]")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_case_expression(self):
        query = parse_query(
            "MATCH (n) RETURN CASE WHEN n.age > 18 THEN 'adult' ELSE 'minor' END AS status"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 1
        item = ret.items[0]
        assert item.alias == "status"
        assert isinstance(item.expression, CaseExpression)
        assert len(item.expression.whens) == 1
        assert item.expression.else_expr is not None

    def test_parse_return_case_multiple_when(self):
        query = parse_query(
            "MATCH (n) RETURN CASE WHEN n.age < 13 THEN 'child' "
            "WHEN n.age < 20 THEN 'teen' ELSE 'adult' END"
        )
        ret = query.clause.return_clause
        item = ret.items[0]
        assert isinstance(item.expression, CaseExpression)
        assert len(item.expression.whens) == 2

    def test_parse_return_case_no_else(self):
        query = parse_query(
            "MATCH (n) RETURN CASE WHEN n.active THEN 'yes' END"
        )
        ret = query.clause.return_clause
        item = ret.items[0]
        assert isinstance(item.expression, CaseExpression)
        assert item.expression.else_expr is None

    def test_parse_return_case_simple(self):
        query = parse_query(
            "MATCH (n) RETURN CASE n.status WHEN 'active' THEN 1 ELSE 0 END"
        )
        ret = query.clause.return_clause
        item = ret.items[0]
        assert isinstance(item.expression, CaseExpression)
        assert item.expression.base_expr is not None
        assert len(item.expression.whens) == 1

    def test_parse_return_temporal_functions(self):
        query = parse_query(
            "MATCH (n) RETURN date('2024-01-02'), time('10:11:12'), "
            "datetime('2024-01-02T10:11:12'), localdatetime('2024-01-02T10:11:12'), "
            "duration('P1DT2H')"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 5

    def test_parse_return_temporal_arithmetic(self):
        query = parse_query(
            "MATCH (n) RETURN date('2024-01-01') + duration('P2D') AS d, "
            "datetime('2024-01-01T00:00:00') - duration('PT1H') AS dt"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 2

    def test_parse_return_map_literal(self):
        query = parse_query("MATCH (n) RETURN {a: 1, b: 2}")
        ret = query.clause.return_clause
        assert len(ret.items) == 1

    def test_parse_return_filter_extract_reduce(self):
        query = parse_query(
            "MATCH (n) RETURN filter(x IN [1,2,3] WHERE x > 1), "
            "extract(x IN [1,2,3] | x), "
            "reduce(acc = 0, x IN [1,2,3] | acc + x)"
        )
        ret = query.clause.return_clause
        assert len(ret.items) == 3


class TestParserCompletQueries:
    """Test parsing complete queries."""

    def test_parse_match_where_return(self):
        query = parse_query("MATCH (n:Person) WHERE n.age > 25 RETURN n.name")
        assert isinstance(query.clause, MatchClause)
        assert query.clause.where_clause is not None
        assert query.clause.return_clause is not None
        assert len(query.clause.return_clause.items) == 1
    
    def test_parse_match_path_variable(self):
        query = parse_query("MATCH p=(a)-[:KNOWS]->(b) RETURN p")
        pattern = query.clause.patterns[0]
        assert pattern.variable == "p"
    
    def test_parse_match_shortest_path(self):
        query = parse_query("MATCH p=shortestPath((a)-[:KNOWS*1..2]->(b)) RETURN p")
        pattern = query.clause.patterns[0]
        assert isinstance(pattern, PatternFunction)
        assert pattern.variable == "p"
    
    def test_parse_match_all_shortest_paths(self):
        query = parse_query("MATCH allShortestPaths((a)-[:KNOWS]->(b)) RETURN a")
        pattern = query.clause.patterns[0]
        assert isinstance(pattern, PatternFunction)

    def test_parse_relationship_where_return(self):
        query = parse_query("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            WHERE a.age > 25
            RETURN a.name, b.name
        """)
        assert isinstance(query.clause, MatchClause)
        assert len(query.clause.patterns[0].elements) == 2
        assert query.clause.where_clause is not None
        assert len(query.clause.return_clause.items) == 2

    def test_parse_union_query(self):
        query = parse_query("""
            MATCH (a:Person) RETURN a.name
            UNION
            MATCH (b:Company) RETURN b.name
        """)
        assert query.union_clauses
        assert len(query.union_clauses) == 1
        assert query.union_clauses[0].all is False

    def test_parse_call_subquery(self):
        query = parse_query("""
            CALL {
                MATCH (n:Person)
                RETURN n.name
            }
        """)
        assert query.clause is not None

    def test_parse_unwind_clause(self):
        query = parse_query("UNWIND [1,2] AS x RETURN x")
        assert isinstance(query.clauses[0], UnwindClause)

    def test_parse_where_case_expression(self):
        query = parse_query(
            "MATCH (n) WHERE CASE n.status WHEN 'active' THEN true ELSE false END RETURN n"
        )
        where = query.clause.where_clause
        assert where is not None
        assert isinstance(where.condition, CaseExpression)


class TestParserErrors:
    """Test parser error handling."""

    def test_invalid_query_start(self):
        with pytest.raises(CypherSyntaxError) as exc_info:
            parse_query("INVALID (n)")
        assert "Expected CREATE, MERGE, DROP, SHOW, CALL, OPTIONAL, MATCH, UNWIND, LOAD, SET, or WITH" in str(exc_info.value)

    def test_missing_parenthesis(self):
        with pytest.raises(CypherSyntaxError) as exc_info:
            parse_query("CREATE n")
        assert "Expected LPAREN" in str(exc_info.value)

    def test_invalid_property_value(self):
        with pytest.raises(CypherSyntaxError) as exc_info:
            parse_query("CREATE (n {name: })")
        assert "Unexpected token in expression" in str(exc_info.value)
