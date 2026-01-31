import pytest

from grafito import GrafitoDatabase


def _make_sample_db() -> GrafitoDatabase:
    db = GrafitoDatabase(":memory:")
    alice = db.create_node(labels=["Person"], properties={"name": "Alice"})
    bob = db.create_node(labels=["Person"], properties={"name": "Bob"})
    db.create_relationship(alice.id, bob.id, "KNOWS", properties={"since": 2021})
    return db


def test_export_turtle_requires_rdflib():
    pytest.importorskip("rdflib")
    from grafito.integrations import export_turtle

    db = _make_sample_db()
    turtle = export_turtle(db, base_uri="grafito:")
    assert "grafito:" in turtle
    assert "KNOWS" in turtle


def test_to_pyvis_requires_pyvis():
    pytest.importorskip("pyvis")
    from grafito.integrations import to_pyvis

    db = _make_sample_db()
    graph = db.to_networkx()
    net = to_pyvis(graph, notebook=False)
    assert hasattr(net, "nodes")
    assert len(net.nodes) == 2


def test_save_pyvis_html():
    pytest.importorskip("pyvis")
    from grafito.integrations import save_pyvis_html
    import os

    db = _make_sample_db()
    graph = db.to_networkx()
    output_path = os.path.join(os.getcwd(), "tmp_pyvis_test.html")
    try:
        result = save_pyvis_html(graph, path=output_path)
        assert result == output_path
        assert output_path and output_path.endswith(".html")
        assert os.path.exists(output_path)
    finally:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
