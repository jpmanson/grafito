from grafito import GrafitoDatabase
from grafito.integrations import save_pyvis_html


def main() -> None:
    db = GrafitoDatabase(":memory:")
    alice = db.create_node(labels=["Person"], properties={"name": "Alice"})
    bob = db.create_node(labels=["Person"], properties={"name": "Bob"})
    company = db.create_node(labels=["Company"], properties={"name": "Acme"})
    db.create_relationship(alice.id, bob.id, "KNOWS")
    db.create_relationship(alice.id, company.id, "WORKS_AT")

    graph = db.to_networkx()
    output_path = save_pyvis_html(graph, path="grafito_graph.html")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
