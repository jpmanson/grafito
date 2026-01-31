"""Tests for dump and restore functionality."""

import os
import tempfile

import pytest

from grafito import GrafitoDatabase
from grafito.cypher.executor import CypherExecutor
from grafito.cypher.exceptions import CypherSyntaxError


class TestDumpRestore:
    """Tests for CypherExecutor.dump() and CypherExecutor.restore()."""

    def test_dump_and_restore_basic(self):
        """Test basic dump and restore of nodes and relationships."""
        # Create source database with sample data
        db1 = GrafitoDatabase(":memory:")
        alice = db1.create_node(labels=["Person"], properties={"name": "Alice", "age": 30})
        bob = db1.create_node(labels=["Person"], properties={"name": "Bob", "age": 25})
        company = db1.create_node(labels=["Company"], properties={"name": "TechCorp"})
        db1.create_relationship(alice.id, bob.id, "KNOWS", {"since": 2020})
        db1.create_relationship(alice.id, company.id, "WORKS_AT", {"position": "Engineer"})

        executor1 = CypherExecutor(db1)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cypher", delete=False) as f:
            dump_path = f.name

        try:
            # Dump
            executor1.dump(dump_path)

            # Verify dump file exists and has content
            assert os.path.exists(dump_path)
            with open(dump_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "CREATE" in content
            assert "Alice" in content
            assert "KNOWS" in content

            # Create fresh database and restore
            db2 = GrafitoDatabase(":memory:")
            executor2 = CypherExecutor(db2)
            executor2.restore(dump_path)

            # Verify restored data
            persons = db2.match_nodes(labels=["Person"])
            assert len(persons) == 2

            companies = db2.match_nodes(labels=["Company"])
            assert len(companies) == 1

            # Verify relationships
            rels = db2.match_relationships(rel_type="KNOWS")
            assert len(rels) == 1
            assert rels[0].properties.get("since") == 2020

            works_at = db2.match_relationships(rel_type="WORKS_AT")
            assert len(works_at) == 1
            assert works_at[0].properties.get("position") == "Engineer"

            # Verify _dump_id is cleaned up
            for node in db2.match_nodes():
                assert "_dump_id" not in node.properties

        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)
            db1.close()
            db2.close()

    def test_dump_with_constraints_and_indexes(self):
        """Test that constraints and indexes are included in dump."""
        db1 = GrafitoDatabase(":memory:")
        db1.create_node_index("Person", "email")
        db1.create_node_uniqueness_constraint("Person", "email")
        db1.create_node(labels=["Person"], properties={"name": "Alice", "email": "alice@test.com"})

        executor1 = CypherExecutor(db1)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cypher", delete=False) as f:
            dump_path = f.name

        try:
            executor1.dump(dump_path)

            with open(dump_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check constraints and indexes are in dump
            assert "CONSTRAINT" in content
            assert "INDEX" in content

            # Restore to new database
            db2 = GrafitoDatabase(":memory:")
            executor2 = CypherExecutor(db2)
            executor2.restore(dump_path)

            # Verify constraints and indexes exist
            constraints = db2.list_constraints()
            assert len(constraints) >= 1

            indexes = db2.list_indexes()
            assert len(indexes) >= 1

        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)
            db1.close()
            db2.close()

    def test_restore_validation_fails_on_syntax_error(self):
        """Test that restore validates script before clearing data."""
        db = GrafitoDatabase(":memory:")
        db.create_node(labels=["Important"], properties={"data": "preserve"})

        executor = CypherExecutor(db)

        # Create invalid script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cypher", delete=False) as f:
            f.write("CREATE (n:Person {name: 'Alice'});\n")
            f.write("INVALID SYNTAX HERE;\n")
            dump_path = f.name

        try:
            # Restore should fail due to syntax error
            with pytest.raises(CypherSyntaxError):
                executor.restore(dump_path)

            # Original data should still exist (not cleared)
            nodes = db.match_nodes(labels=["Important"])
            assert len(nodes) == 1
            assert nodes[0].properties["data"] == "preserve"

        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)
            db.close()

    def test_restore_clear_existing_false(self):
        """Test restore with clear_existing=False appends to existing data."""
        db = GrafitoDatabase(":memory:")
        existing = db.create_node(labels=["Existing"], properties={"name": "Original"})

        executor = CypherExecutor(db)

        # Create valid script with new data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cypher", delete=False) as f:
            f.write("CREATE (:New {name: 'Added'});\n")
            dump_path = f.name

        try:
            executor.restore(dump_path, clear_existing=False)

            # Both old and new data should exist
            existing_nodes = db.match_nodes(labels=["Existing"])
            assert len(existing_nodes) == 1

            new_nodes = db.match_nodes(labels=["New"])
            assert len(new_nodes) == 1

        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)
            db.close()

    def test_dump_complex_properties(self):
        """Test dump handles complex properties (lists, dicts)."""
        db = GrafitoDatabase(":memory:")
        db.create_node(
            labels=["Complex"],
            properties={
                "tags": ["a", "b", "c"],
                "meta": {"score": 100, "active": True},
                "description": "Test with 'quotes' and \"double\""
            }
        )

        executor = CypherExecutor(db)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cypher", delete=False) as f:
            dump_path = f.name

        try:
            executor.dump(dump_path)

            # Restore to new database
            db2 = GrafitoDatabase(":memory:")
            executor2 = CypherExecutor(db2)
            executor2.restore(dump_path)

            nodes = db2.match_nodes(labels=["Complex"])
            assert len(nodes) == 1
            assert nodes[0].properties["tags"] == ["a", "b", "c"]
            assert nodes[0].properties["meta"]["score"] == 100
            assert "quotes" in nodes[0].properties["description"]

        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)
            db.close()
            db2.close()

    def test_dump_empty_database(self):
        """Test dump of empty database."""
        db = GrafitoDatabase(":memory:")
        executor = CypherExecutor(db)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cypher", delete=False) as f:
            dump_path = f.name

        try:
            executor.dump(dump_path)

            with open(dump_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Should have header but no CREATE statements
            assert "Grafito Database Dump" in content

            # Restore should work (no-op)
            db2 = GrafitoDatabase(":memory:")
            executor2 = CypherExecutor(db2)
            executor2.restore(dump_path)

            assert db2.get_node_count() == 0

        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)
            db.close()
            db2.close()
