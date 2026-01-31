"""Visualization helpers (PyVis)."""

from __future__ import annotations

from typing import Any

def to_pyvis(graph, notebook: bool = True, directed: bool = True, **kwargs: Any):
    """Convert a NetworkX graph into a PyVis Network."""
    try:
        from pyvis.network import Network
    except ImportError as exc:
        raise ImportError(
            "pyvis is not installed. Install with `pip install grafito[viz]` "
            "or `uv pip install grafito[viz]`."
        ) from exc
    net = Network(notebook=notebook, directed=directed, **kwargs)
    for node_id, attrs in graph.nodes(data=True):
        labels = attrs.get("labels", [])
        title = attrs.get("properties", {}).get("name", str(node_id))
        net.add_node(node_id, label=str(node_id), title=f"{labels} {title}")
    for source, target, key, attrs in graph.edges(keys=True, data=True):
        rel_type = attrs.get("type", "RELATED_TO")
        net.add_edge(source, target, label=rel_type)
    return net


def save_pyvis_html(
    graph,
    path: str = "grafito_graph.html",
    notebook: bool = False,
    directed: bool = True,
    **kwargs: Any,
) -> str:
    """Render a NetworkX graph to a PyVis HTML file."""
    if "cdn_resources" not in kwargs:
        kwargs["cdn_resources"] = "in_line"
    net = to_pyvis(graph, notebook=notebook, directed=directed, **kwargs)
    html = net.generate_html(notebook=notebook)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return path
