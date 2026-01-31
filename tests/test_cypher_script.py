import os
import uuid

from grafito import GrafitoDatabase


def test_execute_cypher_script_file():
    script = """
    CREATE (n:Person {name: 'Alice'});
    CREATE (n:Person {name: 'Bob'});
    MATCH (n:Person) RETURN n.name ORDER BY n.name;
    """
    base_dir = os.path.join(os.getcwd(), ".grafito", "tmp")
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"script-{uuid.uuid4().hex}.cypher")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(script)

        db = GrafitoDatabase(":memory:")
        results = db.execute_script_file(path)
        assert results[-1] == [{"n.name": "Alice"}, {"n.name": "Bob"}]
        db.close()
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass


def test_execute_cypher_script_ignores_comments():
    script = """
    // Line comment before statement
    CREATE (n:Person {name: 'Alice'});
    /* block
       comment */
    CREATE (n:Person {name: 'Bob'}); -- inline comment
    MATCH (n:Person) RETURN n.name ORDER BY n.name; // trailing comment
    """
    db = GrafitoDatabase(":memory:")
    try:
        results = db.execute_script(script)
        assert results[-1] == [{"n.name": "Alice"}, {"n.name": "Bob"}]
    finally:
        db.close()
