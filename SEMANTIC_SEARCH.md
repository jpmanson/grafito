# Semantic Search in Grafito

## Table of Contents

- [Overview](#overview)
- [The Power of Semantic Search + Knowledge Graphs](#the-power-of-semantic-search--knowledge-graphs)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Embedding Functions](#embedding-functions)
- [Vector Index Backends](#vector-index-backends)
- [Similarity Metrics](#similarity-metrics)
- [Advanced Features](#advanced-features)
- [Cypher Integration](#cypher-integration)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

---

## Overview

Grafito combines the structural power of **property graph databases** with the semantic understanding of **vector embeddings**, enabling a new class of intelligent graph applications. This integration allows you to:

- **Find semantically similar nodes** without exact keyword matches
- **Navigate graphs using meaning** rather than just structure
- **Combine structural and semantic queries** for unprecedented precision
- **Build RAG (Retrieval-Augmented Generation)** systems with rich graph context

### Key Features

- Multiple embedding providers (OpenAI, Cohere, HuggingFace, Ollama, and more)
- Multiple vector index backends (FAISS, HNSWlib, Annoy, LEANN)
- Cosine similarity, L2 distance, and inner product metrics
- Property-based filtering combined with semantic search
- Reranking for improved precision
- Native Cypher integration via `CALL db.vector.search()`
- Persistent and in-memory vector storage

---

## The Power of Semantic Search + Knowledge Graphs

### Why Combine Semantic Search with Knowledge Graphs?

Traditional knowledge graphs excel at **structural reasoning** (finding paths, relationships, patterns), while semantic search excels at **understanding meaning**. Together, they create a powerful synergy:

#### 1. **Semantic Discovery with Structural Navigation**

Find nodes by meaning, then traverse their relationships:

```python
# Find documents about "machine learning" semantically
results = db.semantic_search("machine learning techniques", k=5)

# Then navigate to related entities
for result in results:
    doc_node = result["node"]
    # Find authors of these documents
    authors = db.get_neighbors(doc_node.id, direction="outgoing", rel_type="AUTHORED_BY")
    # Find cited papers
    citations = db.get_neighbors(doc_node.id, direction="outgoing", rel_type="CITES")
```

#### 2. **Context-Aware Retrieval**

Use graph structure to inform semantic search:

```python
# Find papers semantically similar to "neural networks"
papers = db.semantic_search("neural networks", k=10, filter_labels=["Paper"])

# For each paper, get its citation network
for paper_result in papers:
    paper = paper_result["node"]

    # Get papers this paper cites (outgoing edges)
    references = db.get_neighbors(paper.id, direction="outgoing", rel_type="CITES")

    # Get papers that cite this paper (incoming edges)
    cited_by = db.get_neighbors(paper.id, direction="incoming", rel_type="CITES")

    # Find common authors
    authors = db.get_neighbors(paper.id, rel_type="AUTHORED_BY")
```

#### 3. **Multi-Hop Semantic Queries**

Combine semantic similarity with graph traversal:

```cypher
// Find papers semantically similar to a query
CALL db.vector.search('papers_vec', $query_vector, 5)
YIELD node AS paper, score

// Then find co-authors of those papers
MATCH (paper)-[:AUTHORED_BY]->(author)-[:AUTHORED_BY]->(other_paper)
WHERE other_paper <> paper
RETURN paper.title, author.name, collect(other_paper.title) AS coauthor_papers
```

#### 4. **Hybrid Ranking**

Combine semantic similarity with graph metrics (PageRank, centrality, citation count):

```python
results = db.semantic_search("deep learning", k=20)

for result in results:
    node = result["node"]
    semantic_score = result["score"]

    # Calculate graph-based importance
    citation_count = len(db.get_neighbors(node.id, direction="incoming", rel_type="CITES"))

    # Hybrid score
    hybrid_score = 0.7 * semantic_score + 0.3 * (citation_count / 100)

    result["hybrid_score"] = hybrid_score
```

#### 5. **Question Answering with Graph Context**

Build RAG systems with rich relationship context:

```python
# User question: "Who are the leading researchers in reinforcement learning?"
query_vector = embedder(["reinforcement learning research"])[0]

# Find relevant papers semantically
papers = db.semantic_search(query_vector, k=10, filter_labels=["Paper"])

# Get authors and their collaboration networks
for paper in papers:
    authors = db.get_neighbors(paper["node"].id, rel_type="AUTHORED_BY")
    for author in authors:
        # Get author's other papers
        other_papers = db.get_neighbors(author.id, direction="incoming", rel_type="AUTHORED_BY")
        # Get collaboration network
        collaborators = db.execute("""
            MATCH (a:Author {id: $author_id})-[:AUTHORED_BY]-(p:Paper)-[:AUTHORED_BY]-(coauthor:Author)
            WHERE coauthor <> a
            RETURN coauthor, count(p) AS num_collaborations
            ORDER BY num_collaborations DESC
        """, {"author_id": author.id})
```

### Real-World Applications

- **Academic Research**: Semantic paper discovery + citation networks
- **E-commerce**: Product similarity + purchase patterns and user behavior graphs
- **Healthcare**: Symptom matching + patient history and treatment pathways
- **Enterprise Knowledge Management**: Document similarity + organizational hierarchies
- **Recommendation Systems**: Content similarity + social graphs and interaction patterns
- **Fraud Detection**: Anomaly detection + transaction networks
- **Chatbots/Assistants**: Semantic understanding + knowledge graphs for context

---

## Architecture

### How It Works

Grafito's semantic search implementation consists of three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                         Grafito Database                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐     ┌───────────┐  │
│  │   Nodes      │      │  Embeddings  │     │  Vector   │  │
│  │  (SQLite)    │◄────►│   (SQLite)   │────►│  Index    │  │
│  │              │      │              │     │ (Memory)  │  │
│  │ id | props   │      │ node_id |    │     │           │  │
│  │ 1  | {...}   │      │ vector       │     │  FAISS/   │  │
│  │ 2  | {...}   │      │              │     │  HNSW/    │  │
│  └──────────────┘      └──────────────┘     │  Annoy    │  │
│                                              └───────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Embedding Function                        │  │
│  │  (OpenAI / Cohere / HuggingFace / Ollama / etc.)    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Node Creation**: Create nodes with properties (text, metadata)
2. **Embedding Generation**: Convert text properties to vectors using embedding functions
3. **Index Insertion**: Store vectors in specialized vector indexes for fast similarity search
4. **Query**: Convert query text to vector, search index for nearest neighbors
5. **Retrieval**: Return nodes with their properties and similarity scores
6. **Graph Traversal**: Navigate relationships from retrieved nodes

### Storage Model

```sql
-- Nodes store properties as JSON
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY,
    properties TEXT DEFAULT '{}'
);

-- Vector index metadata
CREATE TABLE vector_indexes (
    name TEXT PRIMARY KEY,
    dim INTEGER NOT NULL,
    backend TEXT NOT NULL,      -- 'faiss', 'hnswlib', 'annoy', etc.
    method TEXT NOT NULL,        -- 'flat', 'hnsw', 'ivf_flat', etc.
    options TEXT                 -- JSON: {"metric": "cosine", ...}
);

-- Vector entries (optional persistence)
CREATE TABLE vector_entries (
    index_name TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    vector TEXT NOT NULL,        -- JSON array of floats
    updated_at REAL NOT NULL,
    PRIMARY KEY (index_name, node_id)
);
```

**Note**: The actual vector index (FAISS, HNSW, etc.) is kept in memory for fast searches. The `vector_entries` table provides optional persistence.

---

## Quick Start

### Basic Example

```python
from grafito import GrafitoDatabase
from grafito.embedding_functions import SentenceTransformerEmbeddingFunction
from grafito.indexers import HNSWlibIndexer

# Initialize database
db = GrafitoDatabase(':memory:')

# Create nodes with text content
docs = [
    ("Intro", "Grafito is a lightweight property graph database built on SQLite."),
    ("Vector", "Vector search uses embeddings for semantic similarity queries."),
    ("Cypher", "Cypher is a declarative query language for property graphs."),
]

node_ids = []
for title, text in docs:
    node = db.create_node(
        labels=['Document'],
        properties={'title': title, 'text': text}
    )
    node_ids.append(node.id)

# Initialize embedding function
embedder = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create vector index with cosine similarity
indexer = HNSWlibIndexer(
    options={"metric": "cosine"},
    embedding_function=embedder
)

db.create_vector_index("docs_vec", indexer=indexer)

# Generate embeddings for the 'text' property
texts = [text for _, text in docs]
vectors = embedder(texts)

# Insert embeddings into index
for node_id, vector in zip(node_ids, vectors):
    db.upsert_embedding(node_id, vector, index="docs_vec")

# Perform semantic search
query = "graph database query language"
query_vector = embedder([query])[0]

results = db.semantic_search(query_vector, k=2, index="docs_vec")

# Display results
for rank, result in enumerate(results, 1):
    node = result["node"]
    score = result["score"]
    print(f"{rank}. {node.properties['title']} (score: {score:.4f})")
    print(f"   {node.properties['text']}\n")

db.close()
```

### Output

```
1. Cypher (score: 0.8542)
   Cypher is a declarative query language for property graphs.

2. Intro (score: 0.7231)
   Grafito is a lightweight property graph database built on SQLite.
```

---

## Embedding Functions

Grafito supports multiple embedding providers through a unified interface.

### Available Providers

| Provider | Class | Models |
|----------|-------|--------|
| **Sentence Transformers** | `SentenceTransformerEmbeddingFunction` | All sentence-transformers models |
| **OpenAI** | `OpenAIEmbeddingFunction` | text-embedding-3-small/large, ada-002 |
| **Cohere** | `CohereEmbeddingFunction` | embed-english-v3.0, embed-multilingual-v3.0 |
| **HuggingFace** | `HuggingFaceEmbeddingFunction` | Any HF model with feature extraction |
| **Ollama** | `OllamaEmbeddingFunction` | Local models via Ollama |
| **Jina** | `JinaEmbeddingFunction` | jina-embeddings-v2-base-en |
| **Voyage AI** | `VoyageAIEmbeddingFunction` | voyage-2, voyage-code-2 |
| **Mistral** | `MistralEmbeddingFunction` | mistral-embed |
| **Google GenAI** | `GoogleGenAIEmbeddingFunction` | embedding-001 |
| **Amazon Bedrock** | `AmazonBedrockEmbeddingFunction` | Titan embeddings |
| **TensorFlow Hub** | `TensorFlowHubEmbeddingFunction` | Universal Sentence Encoder |

### Example: OpenAI Embeddings

```python
from grafito.embedding_functions import OpenAIEmbeddingFunction
import os

embedder = OpenAIEmbeddingFunction(
    model_name="text-embedding-3-small",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Generate embeddings
vectors = embedder(["hello world", "machine learning"])
print(f"Dimension: {embedder.dimension}")  # 1536
```

### Example: Local Embeddings with Ollama

```python
from grafito.embedding_functions import OllamaEmbeddingFunction

embedder = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434"
)

vectors = embedder(["graph database", "knowledge graph"])
```

### Example: HuggingFace Sentence Transformers

```python
from grafito.embedding_functions import SentenceTransformerEmbeddingFunction

# Multilingual model
embedder = SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2",
    device="cuda",  # or "cpu"
    normalize_embeddings=True  # Important for cosine similarity
)

vectors = embedder(["knowledge graph", "grafo de conocimiento"])
```

### Embedding Function Interface

All embedding functions implement the same interface:

```python
class EmbeddingFunction(ABC):
    def __call__(self, input: list[str]) -> list[list[float]]:
        """Generate embeddings for input texts."""
        pass

    @property
    def dimension(self) -> int | None:
        """Return embedding dimension."""
        pass

    def default_space(self) -> str:
        """Return default distance metric (e.g., 'cosine', 'l2')."""
        pass
```

---

## Vector Index Backends

Grafito supports multiple vector index backends for different performance and accuracy tradeoffs.

### Backend Comparison

| Backend | Speed | Memory | Precision | Removals | Best For |
|---------|-------|--------|-----------|----------|----------|
| **BruteForce** | Slow | Low | Exact | Yes | Small datasets (<1K) |
| **FAISS** | Fast | Medium | Approximate | Yes | Large datasets, production |
| **HNSWlib** | Very Fast | High | Approximate | No | Real-time search |
| **Annoy** | Fast | Low | Approximate | No | Memory-constrained |
| **LEANN** | Medium | Medium | Approximate | Yes | General purpose |

### 1. HNSWlib (Recommended)

**Hierarchical Navigable Small World** - Fast approximate nearest neighbor search.

```python
from grafito.indexers import HNSWlibIndexer

indexer = HNSWlibIndexer(
    options={
        "metric": "cosine",     # or "l2", "ip"
        "M": 16,                # Number of connections (higher = more accurate, more memory)
        "ef_construction": 200, # Construction time quality
        "ef_search": 50,        # Search time quality
    },
    embedding_function=embedder
)

db.create_vector_index("my_index", indexer=indexer)
```

**Pros**: Very fast search, good accuracy
**Cons**: No support for deletions, higher memory usage

### 2. FAISS (Facebook AI Similarity Search)

**Industry-standard** vector search library with multiple algorithms.

```python
from grafito.indexers import FAISSIndexer

# Flat index (exact search)
indexer = FAISSIndexer(
    method="flat",
    options={"metric": "ip"},  # "l2" or "ip" (inner product)
    embedding_function=embedder
)

# IVF index (approximate, faster for large datasets)
indexer = FAISSIndexer(
    method="ivf_flat",
    options={
        "metric": "l2",
        "nlist": 100,    # Number of clusters
        "nprobe": 10,    # Number of clusters to search
    },
    embedding_function=embedder
)

# HNSW index (fast approximate)
indexer = FAISSIndexer(
    method="hnsw",
    options={
        "metric": "ip",
        "hnsw_m": 32,
        "ef_search": 64,
        "ef_construction": 256,
    },
    embedding_function=embedder
)
```

**Pros**: Very mature, production-ready, supports exact and approximate search
**Cons**: No native cosine similarity (use inner product with normalized vectors)

### 3. Annoy (Approximate Nearest Neighbors Oh Yeah)

**Spotify's** vector search library, optimized for memory efficiency.

```python
from grafito.indexers import AnnoyIndexer

indexer = AnnoyIndexer(
    options={
        "metric": "angular",  # "angular" (cosine), "euclidean", "manhattan", "dot", "hamming"
        "n_trees": 10,        # More trees = higher accuracy, slower build
        "search_k": -1,       # -1 = auto, higher = more accurate search
    },
    embedding_function=embedder
)
```

**Pros**: Very memory efficient, good for read-heavy workloads
**Cons**: Index must be rebuilt for updates

### 4. BruteForce (Exact Search)

Simple exact nearest neighbor search. Best for small datasets or validation.

```python
from grafito.indexers import BruteForceIndexer

indexer = BruteForceIndexer(
    options={"metric": "cosine"},  # or "l2"
    embedding_function=embedder
)
```

**Pros**: Exact results, simple, supports all operations
**Cons**: Slow for large datasets (linear scan)

### 5. LEANN (Lightweight Exact and Approximate NN)

Custom implementation balancing features and performance.

```python
from grafito.indexers import LEANNIndexer

indexer = LEANNIndexer(
    options={
        "metric": "cosine",  # "cosine", "l2", "ip"
        "build_threshold": 1000,  # Switch to approximate after N vectors
    },
    embedding_function=embedder
)
```

---

## Similarity Metrics

### Understanding Distance Metrics

Different metrics measure similarity in different ways:

| Metric | Range | Interpretation | Best For |
|--------|-------|----------------|----------|
| **Cosine Similarity** | [-1, 1] | 1 = identical direction, 0 = orthogonal, -1 = opposite | Text embeddings, normalized vectors |
| **L2 Distance** | [0, ∞) | 0 = identical, larger = more different | General purpose, spatial data |
| **Inner Product** | (-∞, ∞) | Higher = more similar | Normalized vectors (equivalent to cosine) |

### Choosing a Metric

#### Cosine Similarity (Recommended for Text)

Best for text embeddings and semantic search:

```python
# Option 1: HNSWlib with cosine
indexer = HNSWlibIndexer(
    options={"metric": "cosine"},
    embedding_function=embedder
)

# Option 2: Annoy with angular (same as cosine)
indexer = AnnoyIndexer(
    options={"metric": "angular"},
    embedding_function=embedder
)

# Option 3: FAISS with inner product + normalized embeddings
embedder = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    normalize_embeddings=True  # Normalize to unit length
)
indexer = FAISSIndexer(
    method="flat",
    options={"metric": "ip"},  # Inner product with normalized = cosine
    embedding_function=embedder
)
```

**Why cosine for text?**
- Focuses on direction, not magnitude
- Robust to document length differences
- Standard in NLP and semantic search

#### L2 Distance

Euclidean distance, good for spatial embeddings:

```python
indexer = FAISSIndexer(
    method="flat",
    options={"metric": "l2"},
    embedding_function=embedder
)
```

**When to use:**
- Image embeddings
- Spatial data
- When magnitude matters

---

## Advanced Features

### 1. Filtering by Labels and Properties

Combine semantic search with graph structure:

```python
# Find papers about "neural networks" authored by specific authors
results = db.semantic_search(
    query_vector,
    k=10,
    index="papers_vec",
    filter_labels=["Paper", "Published"],
    filter_props={"year": 2023, "conference": "NeurIPS"}
)
```

Using Cypher:

```cypher
CALL db.vector.search('papers_vec', $query_vector, 10, {
    labels: ['Paper', 'Published'],
    properties: {year: 2023, conference: 'NeurIPS'}
})
YIELD node, score
RETURN node.title, node.year, score
```

### 2. Reranking

Improve precision with exact reranking of candidate results:

```python
# Get more candidates, then rerank with exact distances
results = db.semantic_search(
    query_vector,
    k=10,
    index="docs_vec",
    rerank=True,  # Rerank using exact distances
    candidate_multiplier=3  # Fetch 3x candidates before reranking
)
```

**How it works:**
1. Fetch `k * candidate_multiplier` candidates using approximate index
2. Recompute exact distances for all candidates
3. Return top `k` results after reranking

### 3. Custom Rerankers

Register custom reranking functions:

```python
# Define custom reranker
def my_reranker(query_vector, candidate_vectors, candidate_ids):
    """Custom reranking logic."""
    scores = []
    for vec in candidate_vectors:
        # Your custom scoring logic
        score = custom_similarity(query_vector, vec)
        scores.append(score)

    # Return sorted (id, score) pairs
    ranked = sorted(zip(candidate_ids, scores), key=lambda x: x[1], reverse=True)
    return ranked

# Register reranker
db.register_reranker("my_reranker", my_reranker)

# Use in search
results = db.semantic_search(
    query_vector,
    k=10,
    reranker="my_reranker"
)
```

### 4. String Queries (Auto-Embedding)

Pass strings directly instead of vectors:

```python
# String query - automatically embedded
results = db.semantic_search(
    "machine learning algorithms",  # String, not vector!
    k=5,
    index="docs_vec"
)
```

**Requirements**: The vector index must have an associated embedding function.

### 5. Batch Operations

Efficiently insert multiple embeddings:

```python
# Batch insert
db.upsert_embeddings(
    node_ids=[1, 2, 3, 4, 5],
    vectors=[vec1, vec2, vec3, vec4, vec5],
    index="docs_vec"
)
```

### 6. Index Management

```python
# List all vector indexes
indexes = db.list_vector_indexes()
for idx in indexes:
    print(f"{idx['name']}: {idx['dim']}D, {idx['backend']}, {idx['method']}")

# Drop an index
db.drop_vector_index("old_index")

# Get index statistics
stats = db.get_vector_index_stats("docs_vec")
print(f"Total vectors: {stats['count']}")
```

---

## Cypher Integration

Semantic search is available in Cypher via the `db.vector.search()` procedure.

### Basic Usage

```cypher
// Simple vector search
CALL db.vector.search('index_name', $query_vector, 10)
YIELD node, score
RETURN node.title, score
ORDER BY score DESC
```

### With Filtering

```cypher
// Filter by labels and properties
CALL db.vector.search('papers_vec', $query_vector, 10, {
    labels: ['Paper'],
    properties: {year: 2023}
})
YIELD node, score
RETURN node.title, node.authors, score
```

### With Graph Traversal

```cypher
// Find similar papers, then their citations
CALL db.vector.search('papers_vec', $query_vector, 5)
YIELD node AS paper, score

MATCH (paper)-[:CITES]->(cited_paper)
RETURN paper.title, score, collect(cited_paper.title) AS citations
```

### Multi-Hop Semantic Queries

```cypher
// Find papers semantically similar to query
CALL db.vector.search('papers_vec', $query_vector, 10)
YIELD node AS paper, score AS semantic_score

// Then find authors and their collaboration networks
MATCH (paper)-[:AUTHORED_BY]->(author)
MATCH (author)-[:AUTHORED_BY]-(other_paper:Paper)
WHERE other_paper <> paper

RETURN
    paper.title,
    semantic_score,
    author.name,
    count(DISTINCT other_paper) AS num_other_papers
ORDER BY semantic_score DESC
```

### Reranking in Cypher

```cypher
CALL db.vector.search('docs_vec', $query_vector, 10, {
    rerank: true,
    candidate_multiplier: 3
})
YIELD node, score
RETURN node, score
```

---

## Use Cases

### 1. Academic Paper Search

```python
# Create paper nodes
papers = [
    {"title": "Attention Is All You Need", "abstract": "...", "year": 2017},
    {"title": "BERT: Pre-training of Deep Bidirectional Transformers", "abstract": "...", "year": 2018},
    # ... more papers
]

for paper in papers:
    node = db.create_node(labels=["Paper"], properties=paper)

    # Generate embedding from title + abstract
    text = f"{paper['title']}. {paper['abstract']}"
    vector = embedder([text])[0]
    db.upsert_embedding(node.id, vector, index="papers_vec")

# Search semantically
results = db.semantic_search(
    "transformer architecture for NLP",
    k=10,
    index="papers_vec"
)

# Navigate citation network from results
for result in results:
    paper = result["node"]
    citations = db.get_neighbors(paper.id, direction="outgoing", rel_type="CITES")
```

### 2. E-commerce Product Search

```python
# Products with descriptions
products = [
    {"name": "Laptop", "description": "High-performance laptop with 16GB RAM", "category": "Electronics"},
    {"name": "Coffee Maker", "description": "Automatic drip coffee maker", "category": "Kitchen"},
]

for product in products:
    node = db.create_node(labels=["Product"], properties=product)
    vector = embedder([product["description"]])[0]
    db.upsert_embedding(node.id, vector, index="products_vec")

# Natural language search
results = db.semantic_search(
    "machine for brewing coffee automatically",
    k=5,
    filter_labels=["Product"]
)

# Get products frequently bought together
for result in results:
    product = result["node"]
    related = db.get_neighbors(product.id, rel_type="BOUGHT_WITH")
```

### 3. RAG System with Graph Context

```python
def rag_query(user_question: str, k: int = 5):
    """Answer question using graph-enhanced RAG."""

    # 1. Semantic search for relevant documents
    query_vector = embedder([user_question])[0]
    results = db.semantic_search(query_vector, k=k, index="docs_vec")

    # 2. Gather graph context
    context_parts = []
    for result in results:
        doc = result["node"]

        # Document content
        context_parts.append(f"Document: {doc.properties['text']}")

        # Related entities from graph
        related = db.get_neighbors(doc.id, rel_type="MENTIONS")
        if related:
            entities = [n.properties.get('name') for n in related]
            context_parts.append(f"Related entities: {', '.join(entities)}")

        # Source metadata
        sources = db.get_neighbors(doc.id, rel_type="FROM_SOURCE")
        if sources:
            source_names = [s.properties.get('name') for s in sources]
            context_parts.append(f"Sources: {', '.join(source_names)}")

    # 3. Build prompt with rich context
    context = "\n\n".join(context_parts)
    prompt = f"""Context from knowledge graph:
{context}

Question: {user_question}

Answer:"""

    # 4. Send to LLM
    return llm_complete(prompt)
```

### 4. Healthcare: Symptom-Disease Matching

```python
# Create disease nodes with symptom descriptions
diseases = [
    {"name": "Influenza", "symptoms": "fever, cough, sore throat, body aches"},
    {"name": "COVID-19", "symptoms": "fever, dry cough, fatigue, loss of taste or smell"},
]

for disease in diseases:
    node = db.create_node(labels=["Disease"], properties=disease)
    vector = embedder([disease["symptoms"]])[0]
    db.upsert_embedding(node.id, vector, index="diseases_vec")

# Patient presents with symptoms
patient_symptoms = "I have a high temperature, dry cough, and can't taste food"
results = db.semantic_search(patient_symptoms, k=3, index="diseases_vec")

# Get treatment protocols from graph
for result in results:
    disease = result["node"]
    treatments = db.get_neighbors(disease.id, rel_type="TREATED_BY")
    contraindications = db.get_neighbors(disease.id, rel_type="CONTRAINDICATED_WITH")
```

---

## Best Practices

### 1. Choosing the Right Backend

- **Small datasets (<10K vectors)**: BruteForce or FAISS Flat
- **Medium datasets (10K-1M vectors)**: HNSWlib or FAISS HNSW
- **Large datasets (>1M vectors)**: FAISS IVF
- **Memory-constrained**: Annoy
- **Need deletions**: FAISS or BruteForce (avoid HNSWlib/Annoy)

### 2. Choosing the Right Metric

- **Text/semantic search**: Cosine similarity
- **Image embeddings**: L2 distance
- **When in doubt**: Cosine (most universally applicable)

### 3. Normalize Embeddings for Cosine

```python
embedder = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    normalize_embeddings=True  # Essential for accurate cosine similarity
)
```

### 4. Use Reranking for Critical Applications

```python
# Trade speed for accuracy
results = db.semantic_search(
    query,
    k=10,
    rerank=True,
    candidate_multiplier=5  # Fetch 50 candidates, return top 10
)
```

### 5. Batch Insertions

```python
# More efficient than individual inserts
db.upsert_embeddings(node_ids, vectors, index="my_index")
```

### 6. Embed the Right Properties

Choose properties that best represent semantic meaning:

```python
# Good: Embed rich text content
text = f"{paper['title']}. {paper['abstract']}"

# Avoid: Embedding IDs, dates, or non-semantic data
# Bad: text = f"{paper['id']}"  # No semantic meaning
```

### 7. Index Tuning

For HNSW indexes, balance accuracy vs. performance:

```python
# Higher accuracy, slower, more memory
indexer = HNSWlibIndexer(
    options={
        "metric": "cosine",
        "M": 32,               # More connections
        "ef_construction": 400, # Better build quality
        "ef_search": 100,       # Better search quality
    },
    embedding_function=embedder
)

# Faster, less accurate, less memory
indexer = HNSWlibIndexer(
    options={
        "metric": "cosine",
        "M": 8,
        "ef_construction": 100,
        "ef_search": 20,
    },
    embedding_function=embedder
)
```

### 8. Monitor Index Performance

```python
import time

start = time.time()
results = db.semantic_search(query_vector, k=10, index="my_index")
elapsed = time.time() - start

print(f"Search took {elapsed*1000:.2f}ms")
print(f"Throughput: {1/elapsed:.1f} queries/sec")
```

### 9. Combine Semantic + Structural Queries

```python
# Don't just use semantic search - leverage the graph!
results = db.semantic_search("machine learning", k=20)

# Then use graph structure
for result in results:
    node = result["node"]

    # Check connectivity
    connections = db.get_neighbors(node.id)

    # Check paths to important nodes
    has_path = db.find_shortest_path(node.id, important_node_id)

    if len(connections) > 5 and has_path:
        # Node is well-connected and relevant
        print(f"Highly relevant: {node.properties['title']}")
```

### 10. Version Your Embeddings

Track which embedding model was used:

```python
# Store model info in properties
node = db.create_node(
    labels=["Document"],
    properties={
        "text": "...",
        "embedding_model": "text-embedding-3-small",
        "embedding_version": "2024-01-01"
    }
)
```

---

## API Reference

### Database Methods

#### `create_vector_index(name, indexer, dim=None, backend=None, method=None, options=None)`

Create a new vector index.

```python
# With indexer object (recommended)
indexer = HNSWlibIndexer(options={"metric": "cosine"}, embedding_function=embedder)
db.create_vector_index("my_index", indexer=indexer)

# Manual specification
db.create_vector_index(
    "my_index",
    dim=384,
    backend="faiss",
    method="flat",
    options={"metric": "l2"}
)
```

#### `upsert_embedding(node_id, vector, index="default")`

Insert or update embedding for a node.

```python
db.upsert_embedding(node_id, vector, index="my_index")
```

#### `upsert_embeddings(node_ids, vectors, index="default")`

Batch insert/update embeddings.

```python
db.upsert_embeddings([1, 2, 3], [vec1, vec2, vec3], index="my_index")
```

#### `semantic_search(vector, k=None, index="default", filter_labels=None, filter_props=None, exact=False, rerank=False, reranker=None, candidate_multiplier=None)`

Search for nearest neighbors.

```python
results = db.semantic_search(
    vector=query_vector,           # or string if index has embedding function
    k=10,                          # number of results
    index="my_index",              # index name
    filter_labels=["Paper"],       # filter by node labels
    filter_props={"year": 2023},   # filter by properties
    exact=False,                   # use exact search (slower)
    rerank=True,                   # rerank with exact distances
    reranker="my_reranker",        # custom reranker name
    candidate_multiplier=3         # fetch 3x candidates for reranking
)

# Returns: [{"node": Node, "score": float}, ...]
```

#### `list_vector_indexes()`

List all vector indexes.

```python
indexes = db.list_vector_indexes()
# Returns: [{"name": str, "dim": int, "backend": str, "method": str, ...}, ...]
```

#### `drop_vector_index(name)`

Delete a vector index.

```python
db.drop_vector_index("my_index")
```

#### `register_reranker(name, reranker_fn)`

Register a custom reranking function.

```python
def my_reranker(query_vec, candidate_vecs, candidate_ids):
    # Return sorted [(id, score), ...]
    pass

db.register_reranker("my_reranker", my_reranker)
```

### Cypher Syntax

#### `CALL db.vector.search(index, vector, k, options)`

```cypher
// Basic usage
CALL db.vector.search('index_name', $query_vector, 10)
YIELD node, score
RETURN node, score

// With options
CALL db.vector.search('index_name', $query_vector, 10, {
    labels: ['Label1', 'Label2'],
    properties: {key: 'value'},
    rerank: true,
    candidate_multiplier: 3
})
YIELD node, score
RETURN node, score
```

**Options map:**
- `labels`: List of label filters
- `properties`: Map of property filters
- `rerank`: Boolean, enable reranking
- `candidate_multiplier`: Integer, multiplier for candidate fetching

---

## Performance Considerations

### Index Build Time

| Backend | 10K vectors | 100K vectors | 1M vectors |
|---------|-------------|--------------|------------|
| BruteForce | <1s | <5s | ~30s |
| FAISS Flat | <1s | <5s | ~30s |
| FAISS HNSW | ~5s | ~60s | ~10min |
| HNSWlib | ~3s | ~40s | ~7min |
| Annoy | ~2s | ~30s | ~5min |

### Search Latency (1M vectors, k=10)

| Backend | Latency | Accuracy |
|---------|---------|----------|
| BruteForce | ~200ms | 100% (exact) |
| FAISS Flat | ~200ms | 100% (exact) |
| FAISS HNSW | <5ms | ~95% |
| HNSWlib | <3ms | ~95% |
| Annoy | <10ms | ~90% |

*Note: Performance depends on hardware, vector dimensions, and index parameters.*

### Memory Usage (1M vectors, 384D)

| Backend | Memory |
|---------|--------|
| BruteForce | ~1.5GB |
| FAISS Flat | ~1.5GB |
| FAISS HNSW | ~3GB |
| HNSWlib | ~3.5GB |
| Annoy | ~1.8GB |

---

## Troubleshooting

### Common Issues

**Issue**: `ImportError: faiss is not installed`

```bash
# Install FAISS
pip install faiss-cpu  # or faiss-gpu for GPU support
```

**Issue**: `ValueError: metric must be 'l2' or 'ip'`

FAISS doesn't support cosine directly. Use inner product with normalized embeddings:

```python
embedder = SentenceTransformerEmbeddingFunction(
    normalize_embeddings=True  # Normalize to unit length
)
indexer = FAISSIndexer(options={"metric": "ip"})  # Inner product
```

**Issue**: Search returns no results

Check that embeddings were actually inserted:

```python
stats = db.get_vector_index_stats("my_index")
print(f"Vectors in index: {stats['count']}")
```

**Issue**: Low quality results

Try reranking:

```python
results = db.semantic_search(query, k=10, rerank=True, candidate_multiplier=5)
```

---

## Future Enhancements

Potential improvements for semantic search in Grafito:

- **Hybrid search**: Combine semantic and keyword (BM25) search
- **Multi-vector search**: Store multiple embeddings per node
- **Automatic embedding**: Auto-generate embeddings on node creation
- **Dense-sparse hybrid**: Combine dense embeddings with sparse representations
- **GPU acceleration**: FAISS GPU backend support
- **Incremental updates**: Efficient index updates without rebuilds
- **Cross-encoder reranking**: Built-in cross-encoder models
- **Query expansion**: Automatic query reformulation

---

## References

### Academic Papers

- **HNSW**: Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs. *IEEE TPAMI*.
- **FAISS**: Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*.
- **Vector Search Survey**: Li, W., et al. (2020). Approximate nearest neighbor search on high dimensional data—experiments, analyses, and improvement. *IEEE TKDE*.

### Resources

- **Grafito Documentation**: [README.md](README.md)
- **Cypher Coverage**: [docs/grafito_cypher_coverage.html](docs/grafito_cypher_coverage.html)
- **FAISS Documentation**: https://faiss.ai/
- **HNSWlib**: https://github.com/nmslib/hnswlib
- **Sentence Transformers**: https://www.sbert.net/
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

---

## Conclusion

Grafito's semantic search capabilities transform traditional graph queries into intelligent, meaning-aware operations. By combining the structural power of knowledge graphs with the semantic understanding of embeddings, you can build applications that:

- Understand user intent beyond keywords
- Navigate relationships with semantic context
- Provide rich, graph-enhanced retrieval for RAG systems
- Scale from prototypes to production with multiple backends

The integration of semantic search and knowledge graphs represents a powerful paradigm shift in how we query and reason over connected data.

For questions or contributions, please open an issue or pull request on GitHub.
