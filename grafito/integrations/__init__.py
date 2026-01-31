"""Optional integrations."""

__all__ = ["export_rdf", "export_turtle", "to_pyvis", "save_pyvis_html"]


def __getattr__(name: str):
    if name in ("export_rdf", "export_turtle"):
        from .rdf import export_rdf, export_turtle

        return export_rdf if name == "export_rdf" else export_turtle
    if name == "to_pyvis":
        from .viz import to_pyvis

        return to_pyvis
    if name == "save_pyvis_html":
        from .viz import save_pyvis_html

        return save_pyvis_html
    raise AttributeError(f"module {__name__!r} has no attribute {name}")
