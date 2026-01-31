"""Slow semantic search test using Hugging Face embeddings (disabled by default)."""

import orjson
import math

import pytest

from grafito import GrafitoDatabase


@pytest.mark.skip(reason="Slow: requires sentence-transformers and model download.")
def test_semantic_search_hf_example_notebook():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install sentence-transformers to run this test.") from exc

    def sanitize_vector(vector):
        return [float(v) if math.isfinite(float(v)) else 0.0 for v in vector]

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    docs = [
        {"title": "Grafito Overview", "text": "Grafito is a lightweight graph database."},
        {"title": "Cypher Basics", "text": "Cypher is a declarative graph query language."},
        {"title": "Vector Search", "text": "Vector indexes power semantic search workflows."},
    ]
    texts = [item["text"] for item in docs]
    embeddings = [sanitize_vector(vec) for vec in model.encode(texts, normalize_embeddings=True).tolist()]

    db = GrafitoDatabase(":memory:")
    db.create_vector_index(
        "docs_vec",
        dim=len(embeddings[0]),
        backend="faiss",
        method="flat",
        options={"metric": "ip", "store_embeddings": True},
    )

    for item, vector in zip(docs, embeddings):
        node = db.create_node(labels=["Doc"], properties=item)
        db.upsert_embedding(node.id, vector, index="docs_vec")

    query = "semantic search in a graph database"
    query_vec = sanitize_vector(model.encode([query], normalize_embeddings=True)[0].tolist())

    results = db.semantic_search(query_vec, k=2, index="docs_vec", rerank=True)
    assert results

    vector_literal = orjson.dumps(query_vec).decode('utf-8')
    cypher = f"""
    CALL db.vector.search('docs_vec', {vector_literal}, 2, {{labels: ['Doc'], rerank: true}})
    YIELD node, score
    RETURN node.title AS title, score
    """
    cypher_results = db.execute(cypher)
    assert cypher_results
    db.close()
