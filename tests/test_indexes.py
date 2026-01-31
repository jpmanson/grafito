"""Tests for property index API."""

import pytest

from grafito import GrafitoDatabase
from grafito.exceptions import DatabaseError


def _explain_plan(db: GrafitoDatabase, query: str, params: tuple) -> list[str]:
    cursor = db.conn.execute(f"EXPLAIN QUERY PLAN {query}", params)
    return [row[3] for row in cursor.fetchall()]


def test_create_list_drop_node_index():
    db = GrafitoDatabase(':memory:')
    name = db.create_node_index('Person', 'name')
    indexes = db.list_indexes()
    assert any(
        idx['name'] == name
        and idx['entity'] == 'node'
        and idx['label_or_type'] == 'Person'
        and idx['property'] == 'name'
        for idx in indexes
    )
    db.drop_index(name)
    assert all(idx['name'] != name for idx in db.list_indexes())
    db.close()


def test_create_list_relationship_index():
    db = GrafitoDatabase(':memory:')
    name = db.create_relationship_index('KNOWS', 'since')
    indexes = db.list_indexes()
    assert any(
        idx['name'] == name
        and idx['entity'] == 'relationship'
        and idx['label_or_type'] == 'KNOWS'
        and idx['property'] == 'since'
        for idx in indexes
    )
    db.close()


def test_create_index_invalid_identifiers():
    db = GrafitoDatabase(':memory:')
    with pytest.raises(DatabaseError):
        db.create_node_index('Person', 'bad-name')
    with pytest.raises(DatabaseError):
        db.create_relationship_index('KNOWS', '')
    db.close()


def test_node_match_query_uses_property_index():
    db = GrafitoDatabase(':memory:')
    index_name = db.create_node_index(None, 'age')
    db.create_node(labels=['Person'], properties={'age': 30})
    query = "SELECT id FROM nodes n WHERE json_extract(n.properties, '$.age') = ?"
    plan = _explain_plan(db, query, (30,))
    assert any(
        "SEARCH n" in detail and "INDEX" in detail
        for detail in plan
    )
    db.close()


def test_relationship_match_query_uses_property_index():
    db = GrafitoDatabase(':memory:')
    index_name = db.create_relationship_index(None, 'since')
    a = db.create_node(labels=['Person'], properties={'name': 'A'})
    b = db.create_node(labels=['Person'], properties={'name': 'B'})
    db.create_relationship(a.id, b.id, 'KNOWS', {'since': 2020})
    query = (
        "SELECT id, source_node_id, target_node_id, type, properties "
        "FROM relationships WHERE json_extract(properties, '$.since') = ?"
    )
    plan = _explain_plan(db, query, (2020,))
    assert any(
        "SEARCH" in detail and "relationships" in detail and "INDEX" in detail
        for detail in plan
    )
    db.close()


def test_node_match_label_property_uses_indexes():
    db = GrafitoDatabase(':memory:')
    index_name = db.create_node_index(None, 'age')
    db.create_node(labels=['Person'], properties={'age': 30})
    query = """
        SELECT DISTINCT n.id
        FROM nodes n
        JOIN node_labels nl ON n.id = nl.node_id
        JOIN labels l ON nl.label_id = l.id
        WHERE l.name IN (?)
          AND json_extract(n.properties, '$.age') = ?
        GROUP BY n.id
        HAVING COUNT(DISTINCT l.name) = ?
    """
    plan = _explain_plan(db, query, ('Person', 30, 1))
    assert any(index_name in detail for detail in plan)
    assert any('labels' in detail or 'node_labels' in detail for detail in plan)
    db.close()
