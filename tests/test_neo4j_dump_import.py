from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from grafito import GrafitoDatabase


def test_neo4j_dump_import_limited() -> None:
    dump_path = Path("examples") / "recommendations-5.26.dump"
    if not dump_path.exists():
        pytest.skip("Neo4j dump fixture not found.")
    pytest.importorskip("zstandard")

    temp_dir = Path(".grafito") / f"neo4j_dump_test_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        db = GrafitoDatabase(":memory:")
        db.import_neo4j_dump(
            str(dump_path),
            temp_dir=str(temp_dir),
            cleanup=False,
            node_limit=200,
            rel_limit=200,
        )
        assert db.get_node_count() == 200
        assert db.get_relationship_count() == 200
        assert db.get_node_count("Movie") > 0
        assert db.get_relationship_count("IN_GENRE") > 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
