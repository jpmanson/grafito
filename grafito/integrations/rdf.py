"""RDF/Turtle import/export helpers."""

from __future__ import annotations

import orjson
from typing import Any

from ..database import GrafitoDatabase


def export_rdf(
    db: GrafitoDatabase,
    base_uri: str = "grafito:",
    node_prefix: str = "node/",
    rel_prefix: str = "rel/",
    prefixes: dict[str, str] | None = None,
) -> "Graph":
    """Export the Grafito graph to an rdflib Graph."""
    try:
        from rdflib import Graph, Literal, Namespace, RDF, URIRef
    except ImportError as exc:
        raise ImportError("rdflib is not installed. Install with `pip install rdflib`.") from exc
    graph = Graph()
    ns = Namespace(base_uri)
    rdf_key = "__rdf__"

    default_prefixes = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "schema": "http://schema.org/",
    }
    merged_prefixes = default_prefixes.copy()
    if isinstance(prefixes, dict):
        merged_prefixes.update(prefixes)
    for prefix, uri in merged_prefixes.items():
        if prefix is None:
            continue
        graph.bind(prefix, uri)
    graph.bind("", base_uri)

    def resolve_term(term: str, prefixes: dict[str, str]) -> URIRef:
        if "://" in term or term.startswith("urn:"):
            return URIRef(term)
        if ":" in term:
            prefix, local = term.split(":", 1)
            if prefix in prefixes:
                return URIRef(prefixes[prefix] + local)
        return URIRef(f"{base_uri}{term}")

    def add_rdf_values(
        subject: URIRef,
        predicate: URIRef,
        value: Any,
        prefixes: dict[str, str],
    ) -> None:
        if isinstance(value, list):
            for item in value:
                add_rdf_values(subject, predicate, item, prefixes)
            return
        if isinstance(value, dict):
            if "@id" in value:
                obj = resolve_term(str(value["@id"]), prefixes)
                graph.add((subject, predicate, obj))
                return
            if "@value" in value:
                datatype = value.get("@type")
                lang = value.get("@lang") or value.get("@language")
                datatype_ref = resolve_term(str(datatype), prefixes) if datatype else None
                graph.add((subject, predicate, Literal(value["@value"], datatype=datatype_ref, lang=lang)))
                return
        graph.add((subject, predicate, Literal(value)))

    node_uris: dict[int, str] = {}
    cursor = db.conn.execute("SELECT id, properties, uri FROM nodes ORDER BY id")
    for row in cursor.fetchall():
        node_id = int(row["id"])
        node_uri_value = row["uri"] or f"{base_uri}{node_prefix}{node_id}"
        node_uris[node_id] = node_uri_value
        node_uri = URIRef(node_uri_value)
        labels = db._get_node_labels(node_id)
        for label in labels:
            graph.add((node_uri, RDF.type, ns[label]))
        properties = row["properties"]
        if properties:
            prop_map = orjson.loads(properties)
            for key, value in prop_map.items():
                if key == rdf_key:
                    continue
                graph.add((node_uri, ns[key], Literal(value)))
            rdf_block = prop_map.get(rdf_key)
            if isinstance(rdf_block, dict):
                context = rdf_block.get("@context")
                prefixes = merged_prefixes.copy()
                if isinstance(context, dict):
                    prefixes.update(context)
                for key, value in rdf_block.items():
                    if key.startswith("@"):
                        continue
                    predicate = resolve_term(key, prefixes)
                    add_rdf_values(node_uri, predicate, value, prefixes)

    cursor = db.conn.execute(
        "SELECT id, source_node_id, target_node_id, type, properties, uri FROM relationships ORDER BY id"
    )
    for row in cursor.fetchall():
        rel_id = int(row["id"])
        source_uri = URIRef(
            node_uris.get(int(row["source_node_id"]))
            or f"{base_uri}{node_prefix}{int(row['source_node_id'])}"
        )
        target_uri = URIRef(
            node_uris.get(int(row["target_node_id"]))
            or f"{base_uri}{node_prefix}{int(row['target_node_id'])}"
        )
        pred = ns[row["type"]]
        graph.add((source_uri, pred, target_uri))
        props = row["properties"]
        if props:
            prop_map = orjson.loads(props)
            rel_uri_value = row["uri"] or f"{base_uri}{rel_prefix}{rel_id}"
            rel_uri = URIRef(rel_uri_value)
            graph.add((rel_uri, RDF.type, ns[row["type"]]))
            graph.add((rel_uri, ns["source"], source_uri))
            graph.add((rel_uri, ns["target"], target_uri))
            for key, value in prop_map.items():
                if key == rdf_key:
                    continue
                graph.add((rel_uri, ns[key], Literal(value)))
            rdf_block = prop_map.get(rdf_key)
            if isinstance(rdf_block, dict):
                context = rdf_block.get("@context")
                prefixes = merged_prefixes.copy()
                if isinstance(context, dict):
                    prefixes.update(context)
                for key, value in rdf_block.items():
                    if key.startswith("@"):
                        continue
                    predicate = resolve_term(key, prefixes)
                    add_rdf_values(rel_uri, predicate, value, prefixes)

    return graph


def export_turtle(
    db: GrafitoDatabase,
    base_uri: str = "grafito:",
    prefixes: dict[str, str] | None = None,
) -> str:
    """Export the Grafito graph to Turtle."""
    graph = export_rdf(db, base_uri=base_uri, prefixes=prefixes)
    return graph.serialize(format="turtle")
