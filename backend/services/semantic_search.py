"""
Semantic search using sentence-transformers.
Falls back to keyword matching if sentence-transformers is not installed.
"""
from typing import List

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _model = None
    SEMANTIC_AVAILABLE = True

    def get_model() -> SentenceTransformer:
        global _model
        if _model is None:
            print("Loading sentence-transformers model (first run takes ~30s)...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ Model loaded")
        return _model

    def embed_text(text: str) -> List[float]:
        model = get_model()
        return model.encode(text, convert_to_numpy=True).tolist()

    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        a = np.array(vec1)
        b = np.array(vec2)
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

except ImportError:
    SEMANTIC_AVAILABLE = False
    print("⚠️  sentence-transformers not installed — semantic search disabled. Keyword search will be used.")

    def embed_text(text: str) -> List[float]:
        return []

    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        return 0.0


def rank_products_by_query(query: str, products: list) -> list:
    """Rank products by semantic similarity to query. Falls back to keyword match."""
    if not SEMANTIC_AVAILABLE:
        # Simple keyword fallback
        q = query.lower()
        def keyword_score(p):
            text = f"{p.get('name','')} {p.get('description','')} {' '.join(p.get('tags',[]))}".lower()
            return sum(1 for word in q.split() if word in text)
        return sorted(products, key=keyword_score, reverse=True)

    query_embedding = embed_text(query)
    scored = []
    for p in products:
        emb = p.get("embedding")
        score = cosine_similarity(query_embedding, emb) if emb else 0.0
        scored.append({**p, "_score": score})
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored
