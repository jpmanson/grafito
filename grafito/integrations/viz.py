"""Visualization helpers (PyVis)."""

from __future__ import annotations

from typing import Any, Callable, Protocol
import json
import shutil
import subprocess

_DEFAULT_COLORS = [
    "#8ecae6",
    "#219ebc",
    "#023047",
    "#ffb703",
    "#fb8500",
    "#90be6d",
    "#f94144",
    "#577590",
    "#43aa8b",
    "#f3722c",
]


def to_pyvis(
    graph,
    notebook: bool = True,
    directed: bool = True,
    node_label: str = "id",
    label_attr: str | None = None,
    label_fn: Callable[[Any, dict[str, Any]], str] | None = None,
    node_color_attr: str | None = None,
    color_map: dict[str, str] | None = None,
    color_by_label: bool = False,
    default_color: str = "#8ecae6",
    palette: list[str] | None = None,
    **kwargs: Any,
):
    """Convert a NetworkX graph into a PyVis Network."""
    try:
        from pyvis.network import Network
    except ImportError as exc:
        raise ImportError(
            "pyvis is not installed. Install with `pip install grafito[viz]` "
            "or `uv pip install grafito[viz]`."
        ) from exc
    net = Network(notebook=notebook, directed=directed, **kwargs)
    palette = palette or _DEFAULT_COLORS
    label_colors: dict[str, str] = {}

    def pick_label_color(labels: list[str]) -> str:
        if not labels:
            return default_color
        for label in labels:
            if color_map and label in color_map:
                return color_map[label]
        if not color_by_label:
            return default_color
        label = labels[0]
        if label not in label_colors:
            label_colors[label] = palette[len(label_colors) % len(palette)]
        return label_colors[label]

    def resolve_label(node_id: Any, attrs: dict[str, Any]) -> str:
        if label_fn:
            return str(label_fn(node_id, attrs))
        properties = attrs.get("properties", {})
        if label_attr:
            if label_attr in attrs:
                return str(attrs[label_attr])
            if label_attr in properties:
                return str(properties[label_attr])
        if node_label == "name":
            return str(properties.get("name", node_id))
        if node_label == "labels":
            labels = attrs.get("labels", [])
            return ":".join(labels) if labels else str(node_id)
        if node_label == "label_and_name":
            labels = attrs.get("labels", [])
            label_prefix = ":".join(labels) + " " if labels else ""
            return f"{label_prefix}{properties.get('name', node_id)}"
        return str(node_id)

    for node_id, attrs in graph.nodes(data=True):
        labels = attrs.get("labels", [])
        title = attrs.get("properties", {}).get("name", str(node_id))
        color = default_color
        if node_color_attr:
            props = attrs.get("properties", {})
            color = props.get(node_color_attr) or attrs.get(node_color_attr) or default_color
        else:
            color = pick_label_color(labels)
        net.add_node(
            node_id,
            label=resolve_label(node_id, attrs),
            title=f"{labels} {title}",
            color=color,
        )
    for source, target, key, attrs in graph.edges(keys=True, data=True):
        rel_type = attrs.get("type", "RELATED_TO")
        net.add_edge(source, target, label=rel_type)
    return net


_PHYSICS_PRESETS = {
    "compact": {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.4,
                "springLength": 80,
                "springConstant": 0.04,
            }
        }
    },
    "spread": {
        "physics": {
            "repulsion": {
                "nodeDistance": 200,
                "springLength": 200,
                "springConstant": 0.01,
            }
        }
    },
}


class VizBackend(Protocol):
    """Visualization backend interface."""

    name: str

    def render(self, graph, **kwargs: Any) -> Any:
        """Render graph and return backend-specific object."""

    def export(self, graph, path: str, **kwargs: Any) -> str:
        """Render graph and save to a file path."""


class PyVisBackend:
    """PyVis backend adapter."""

    name = "pyvis"

    def render(self, graph, **kwargs: Any):
        return to_pyvis(graph, **kwargs)

    def export(self, graph, path: str, **kwargs: Any) -> str:
        return save_pyvis_html(graph, path=path, **kwargs)

class D2Backend:
    """D2 backend adapter (text export, optional render via d2 CLI)."""

    name = "d2"

    def render(self, graph, **kwargs: Any) -> str:
        return graph_to_d2(graph, **kwargs)

    def export(self, graph, path: str, **kwargs: Any) -> str:
        d2_kwargs = dict(kwargs)
        d2_kwargs.pop("render", None)
        d2_kwargs.pop("theme", None)
        d2_text = graph_to_d2(graph, **d2_kwargs)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(d2_text)
        render = kwargs.get("render")
        if render:
            render_d2(path, render=render, theme=kwargs.get("theme"))
        return path

class MermaidBackend:
    """Mermaid backend adapter (text export, optional render via mmdc CLI)."""

    name = "mermaid"

    def render(self, graph, **kwargs: Any) -> str:
        return graph_to_mermaid(graph, **kwargs)

    def export(self, graph, path: str, **kwargs: Any) -> str:
        mermaid_kwargs = dict(kwargs)
        mermaid_kwargs.pop("render", None)
        mermaid_text = graph_to_mermaid(graph, **mermaid_kwargs)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(mermaid_text)
        render = kwargs.get("render")
        if render:
            render_mermaid(path, render=render, theme=kwargs.get("theme"))
        return path

class GraphvizBackend:
    """Graphviz DOT backend adapter (text export, optional render via dot CLI)."""

    name = "graphviz"

    def render(self, graph, **kwargs: Any) -> str:
        return graph_to_dot(graph, **kwargs)

    def export(self, graph, path: str, **kwargs: Any) -> str:
        dot_kwargs = dict(kwargs)
        dot_kwargs.pop("render", None)
        dot_text = graph_to_dot(graph, **dot_kwargs)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(dot_text)
        render = kwargs.get("render")
        if render:
            render_dot(path, render=render)
        return path


_VIZ_BACKENDS: dict[str, VizBackend] = {
    "pyvis": PyVisBackend(),
    "d2": D2Backend(),
    "mermaid": MermaidBackend(),
    "graphviz": GraphvizBackend(),
}


def register_viz_backend(name: str, backend: VizBackend, override: bool = False) -> None:
    """Register a visualization backend."""
    if not name:
        raise ValueError("Backend name cannot be empty")
    if not override and name in _VIZ_BACKENDS:
        raise ValueError(f"Backend '{name}' already registered")
    _VIZ_BACKENDS[name] = backend


def available_viz_backends() -> list[str]:
    """List registered visualization backends."""
    return sorted(_VIZ_BACKENDS.keys())


def render_graph(graph, backend: str = "pyvis", **kwargs: Any) -> Any:
    """Render a graph using a registered backend and return its object."""
    if backend not in _VIZ_BACKENDS:
        available = ", ".join(available_viz_backends())
        raise ValueError(f"Unknown backend '{backend}'. Available: {available}")
    return _VIZ_BACKENDS[backend].render(graph, **kwargs)


def export_graph(
    graph,
    path: str,
    backend: str = "pyvis",
    **kwargs: Any,
) -> str:
    """Render a graph using a registered backend and save to a file."""
    if backend not in _VIZ_BACKENDS:
        available = ", ".join(available_viz_backends())
        raise ValueError(f"Unknown backend '{backend}'. Available: {available}")
    return _VIZ_BACKENDS[backend].export(graph, path, **kwargs)


def _safe_d2_id(value: Any) -> str:
    text = str(value).replace("\"", "'")
    return f"\"{text}\""


def graph_to_d2(
    graph,
    node_label: str = "id",
    label_attr: str | None = None,
    label_fn: Callable[[Any, dict[str, Any]], str] | None = None,
    include_properties: bool = False,
) -> str:
    """Serialize a NetworkX graph to D2 text."""
    lines: list[str] = ["direction: right"]

    def resolve_label(node_id: Any, attrs: dict[str, Any]) -> str:
        if label_fn:
            return str(label_fn(node_id, attrs))
        properties = attrs.get("properties", {})
        if label_attr:
            if label_attr in attrs:
                return str(attrs[label_attr])
            if label_attr in properties:
                return str(properties[label_attr])
        if node_label == "name":
            return str(properties.get("name", node_id))
        if node_label == "labels":
            labels = attrs.get("labels", [])
            return ":".join(labels) if labels else str(node_id)
        if node_label == "label_and_name":
            labels = attrs.get("labels", [])
            label_prefix = ":".join(labels) + " " if labels else ""
            return f"{label_prefix}{properties.get('name', node_id)}"
        return str(node_id)

    for node_id, attrs in graph.nodes(data=True):
        node_key = _safe_d2_id(node_id)
        label = resolve_label(node_id, attrs)
        lines.append(f"{node_key}: { _safe_d2_id(label) }")
        if include_properties:
            props = attrs.get("properties", {})
            for key, value in props.items():
                lines.append(f"{node_key}.{key}: { _safe_d2_id(value) }")

    for source, target, key, attrs in graph.edges(keys=True, data=True):
        rel_type = attrs.get("type", "RELATED_TO")
        lines.append(f"{_safe_d2_id(source)} -> {_safe_d2_id(target)}: { _safe_d2_id(rel_type) }")

    return "\n".join(lines) + "\n"


def render_d2(path: str, render: str = "svg", theme: str | None = None) -> str:
    """Render a .d2 file using the d2 CLI."""
    binary = shutil.which("d2")
    if not binary:
        raise RuntimeError(
            "d2 CLI not found. Install with `brew install d2` and ensure it is on PATH."
        )
    output = path.rsplit(".", 1)[0] + f".{render}"
    cmd = [binary, path, output]
    if theme:
        cmd.extend(["--theme", theme])
    subprocess.run(cmd, check=True)
    return output


def graph_to_mermaid(
    graph,
    node_label: str = "id",
    label_attr: str | None = None,
    label_fn: Callable[[Any, dict[str, Any]], str] | None = None,
    include_properties: bool = False,
    direction: str = "LR",
) -> str:
    """Serialize a NetworkX graph to Mermaid flowchart text."""
    lines: list[str] = [f"flowchart {direction}"]

    def resolve_label(node_id: Any, attrs: dict[str, Any]) -> str:
        if label_fn:
            return str(label_fn(node_id, attrs))
        properties = attrs.get("properties", {})
        if label_attr:
            if label_attr in attrs:
                return str(attrs[label_attr])
            if label_attr in properties:
                return str(properties[label_attr])
        if node_label == "name":
            return str(properties.get("name", node_id))
        if node_label == "labels":
            labels = attrs.get("labels", [])
            return ":".join(labels) if labels else str(node_id)
        if node_label == "label_and_name":
            labels = attrs.get("labels", [])
            label_prefix = ":".join(labels) + " " if labels else ""
            return f"{label_prefix}{properties.get('name', node_id)}"
        return str(node_id)

    def mermaid_id(value: Any) -> str:
        text = str(value)
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in text)
        return f"n_{safe}" if safe and safe[0].isdigit() else safe or "n"

    node_ids: dict[Any, str] = {}
    for node_id, attrs in graph.nodes(data=True):
        m_id = mermaid_id(node_id)
        node_ids[node_id] = m_id
        label = resolve_label(node_id, attrs)
        lines.append(f'{m_id}["{label}"]')
        if include_properties:
            props = attrs.get("properties", {})
            for key, value in props.items():
                lines.append(f'{m_id} -- "{key}" --> {mermaid_id(f"{m_id}_{key}")}["{value}"]')

    for source, target, key, attrs in graph.edges(keys=True, data=True):
        rel_type = attrs.get("type", "RELATED_TO")
        lines.append(f'{node_ids.get(source)} -- "{rel_type}" --> {node_ids.get(target)}')

    return "\n".join(lines) + "\n"


def render_mermaid(path: str, render: str = "svg", theme: str | None = None) -> str:
    """Render a .mmd file using the mermaid-cli (mmdc)."""
    binary = shutil.which("mmdc")
    if not binary:
        raise RuntimeError(
            "mermaid-cli (mmdc) not found. Install with `npm i -g @mermaid-js/mermaid-cli`."
        )
    output = path.rsplit(".", 1)[0] + f".{render}"
    cmd = [binary, "-i", path, "-o", output]
    if theme:
        cmd.extend(["-t", theme])
    subprocess.run(cmd, check=True)
    return output


def graph_to_dot(
    graph,
    node_label: str = "id",
    label_attr: str | None = None,
    label_fn: Callable[[Any, dict[str, Any]], str] | None = None,
    include_properties: bool = False,
    directed: bool = True,
) -> str:
    """Serialize a NetworkX graph to Graphviz DOT text."""
    graph_type = "digraph" if directed else "graph"
    edge_op = "->" if directed else "--"
    lines: list[str] = [f"{graph_type} grafito {{"]

    def resolve_label(node_id: Any, attrs: dict[str, Any]) -> str:
        if label_fn:
            return str(label_fn(node_id, attrs))
        properties = attrs.get("properties", {})
        if label_attr:
            if label_attr in attrs:
                return str(attrs[label_attr])
            if label_attr in properties:
                return str(properties[label_attr])
        if node_label == "name":
            return str(properties.get("name", node_id))
        if node_label == "labels":
            labels = attrs.get("labels", [])
            return ":".join(labels) if labels else str(node_id)
        if node_label == "label_and_name":
            labels = attrs.get("labels", [])
            label_prefix = ":".join(labels) + " " if labels else ""
            return f"{label_prefix}{properties.get('name', node_id)}"
        return str(node_id)

    for node_id, attrs in graph.nodes(data=True):
        label = resolve_label(node_id, attrs).replace("\"", "\\\"")
        lines.append(f'  "{node_id}" [label="{label}"];')
        if include_properties:
            props = attrs.get("properties", {})
            for key, value in props.items():
                prop_node = f"{node_id}_{key}"
                lines.append(f'  "{prop_node}" [label="{value}"];')
                lines.append(f'  "{node_id}" {edge_op} "{prop_node}" [label="{key}"];')

    for source, target, key, attrs in graph.edges(keys=True, data=True):
        rel_type = attrs.get("type", "RELATED_TO").replace("\"", "\\\"")
        lines.append(f'  "{source}" {edge_op} "{target}" [label="{rel_type}"];')

    lines.append("}")
    return "\n".join(lines) + "\n"


def render_dot(path: str, render: str = "svg") -> str:
    """Render a .dot file using the Graphviz dot CLI."""
    binary = shutil.which("dot")
    if not binary:
        raise RuntimeError(
            "Graphviz 'dot' not found. Install with `brew install graphviz`."
        )
    output = path.rsplit(".", 1)[0] + f".{render}"
    cmd = [binary, f"-T{render}", path, "-o", output]
    subprocess.run(cmd, check=True)
    return output


def save_pyvis_html(
    graph,
    path: str = "grafito_graph.html",
    notebook: bool = False,
    directed: bool = True,
    physics: str | dict[str, Any] | None = None,
    **kwargs: Any,
) -> str:
    """Render a NetworkX graph to a PyVis HTML file."""
    if "cdn_resources" not in kwargs:
        kwargs["cdn_resources"] = "in_line"
    net = to_pyvis(graph, notebook=notebook, directed=directed, **kwargs)
    if isinstance(physics, dict):
        net.set_options(json.dumps(physics))
    elif isinstance(physics, str):
        if physics in _PHYSICS_PRESETS:
            net.set_options(json.dumps(_PHYSICS_PRESETS[physics]))
        elif physics == "barnes_hut":
            net.barnes_hut()
        elif physics == "repulsion":
            net.repulsion()
        elif physics == "force_atlas_2based":
            net.force_atlas_2based()
    html = net.generate_html(notebook=notebook)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return path
