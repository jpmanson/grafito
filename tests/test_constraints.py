"""Tests for schema constraints API."""

import pytest

from grafito import GrafitoDatabase
from grafito.exceptions import ConstraintError


def test_create_list_drop_constraint():
    db = GrafitoDatabase(':memory:')
    name = db.create_node_existence_constraint('Person', 'name')
    constraints = db.list_constraints()
    assert any(c['name'] == name and c['type'] == 'EXISTS' for c in constraints)
    db.drop_constraint(name)
    assert all(c['name'] != name for c in db.list_constraints())
    db.close()


def test_uniqueness_constraint_violation():
    db = GrafitoDatabase(':memory:')
    db.create_node(labels=['Person'], properties={'email': 'a@example.com'})
    db.create_node_uniqueness_constraint('Person', 'email')
    with pytest.raises(ConstraintError):
        db.create_node(labels=['Person'], properties={'email': 'a@example.com'})
    db.close()


def test_existence_constraint_violation():
    db = GrafitoDatabase(':memory:')
    db.create_node_existence_constraint('Person', 'name')
    with pytest.raises(ConstraintError):
        db.create_node(labels=['Person'], properties={'age': 30})
    db.close()


def test_type_constraint_violation():
    db = GrafitoDatabase(':memory:')
    db.create_node_type_constraint('Person', 'age', 'INTEGER')
    with pytest.raises(ConstraintError):
        db.create_node(labels=['Person'], properties={'age': 'old'})
    db.close()
