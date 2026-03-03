from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

# Load model once at module level (cached)
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Loading sentence-transformers model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded")
    return _model

def embed_text(text: str) -> List[float]:
    """Generate embedding for a text string."""
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def rank_products_by_query(query: str, products: list) -> list:
    """
    Rank a list of product dicts by semantic similarity to the query.
    Each product must have a stored 'embedding' field.
    """
    query_embedding = embed_text(query)
    scored = []
    for p in products:
        emb = p.get("embedding")
        if emb:
            score = cosine_similarity(query_embedding, emb)
        else:
            score = 0.0
        scored.append({**p, "_score": score})
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored
