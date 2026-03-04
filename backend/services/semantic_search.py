"""
Intent-Based Semantic Search Service.
Uses sentence-transformers (all-MiniLM-L6-v2) with normalized embeddings
for accurate cosine similarity via fast dot-product.

Key features:
  - Normalized embeddings (L2) → dot-product == cosine similarity
  - Intent boost map: symptom/diet/mood keywords → product tag multipliers
  - Configurable similarity threshold
  - Model cached globally (loaded once on first use)
"""
from typing import List, Dict, Any
import numpy as np

# ── Model setup ──────────────────────────────────────────────────────────────
_model = None
SEMANTIC_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    print("⚠️  sentence-transformers not installed — keyword fallback active.")


def get_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        print("🔄 Loading sentence-transformers model (cached after first load)…")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Semantic model loaded.")
    return _model


def embed_text(text: str) -> List[float]:
    """Generate a normalized embedding for a text string."""
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
    return vec.tolist()


# ── Intent Boost Map ─────────────────────────────────────────────────────────
# Maps common user intent keywords → product tags/name fragments to boost.
# Each match multiplies the product's score by the given factor.
INTENT_BOOSTS: Dict[str, Dict[str, float]] = {
    # Illness / cold / immunity
    "cold":        {"honey": 1.6, "ginger": 1.6, "tulsi": 1.5, "turmeric": 1.5, "vitamin c": 1.4, "cough": 1.5, "immunity": 1.4, "lemon": 1.3},
    "cough":       {"honey": 1.6, "ginger": 1.5, "tulsi": 1.5, "cough": 1.6, "turmeric": 1.4},
    "fever":       {"paracetamol": 1.7, "ibuprofen": 1.6, "electrolyte": 1.5, "vitamin c": 1.4, "turmeric": 1.3},
    "sick":        {"honey": 1.4, "ginger": 1.4, "turmeric": 1.4, "vitamin c": 1.4, "tulsi": 1.4},
    "headache":    {"paracetamol": 1.7, "ibuprofen": 1.6, "electrolyte": 1.4, "water": 1.3},
    "immunity":    {"vitamin c": 1.5, "tulsi": 1.5, "turmeric": 1.5, "honey": 1.4, "ginger": 1.4},
    "sore throat": {"honey": 1.6, "ginger": 1.5, "tulsi": 1.5, "lemon": 1.4},

    # Energy / gym / weakness
    "tired":       {"energy": 1.6, "protein": 1.5, "multivitamin": 1.5, "electrolyte": 1.4, "banana": 1.3, "almond": 1.3},
    "weak":        {"protein": 1.5, "energy": 1.5, "multivitamin": 1.5, "electrolyte": 1.4, "vitamin": 1.4},
    "gym":         {"protein": 1.7, "whey": 1.7, "energy": 1.5, "almond": 1.4, "banana": 1.3},
    "workout":     {"protein": 1.6, "whey": 1.6, "energy": 1.5, "banana": 1.3},
    "muscle":      {"whey": 1.7, "protein": 1.7, "creatine": 1.6, "almond": 1.3},

    # Diet / weight loss
    "weight loss": {"green tea": 1.6, "oats": 1.5, "chia": 1.5, "quinoa": 1.5, "salad": 1.4, "protein": 1.3},
    "diet":        {"green tea": 1.5, "oats": 1.5, "salad": 1.5, "quinoa": 1.4, "chia": 1.4},
    "slim":        {"green tea": 1.5, "oats": 1.4, "chia": 1.4, "quinoa": 1.4},
    "healthy":     {"salad": 1.4, "oats": 1.4, "green tea": 1.4, "vitamin": 1.3, "fruit": 1.3},
    "keto":        {"avocado": 1.6, "almond": 1.5, "egg": 1.5, "cheese": 1.4},

    # Hydration
    "thirsty":     {"water": 1.6, "electrolyte": 1.5, "juice": 1.4, "coconut": 1.4},
    "dehydrated":  {"electrolyte": 1.7, "water": 1.6, "coconut water": 1.5},
}

SIMILARITY_THRESHOLD = 0.20  # Minimum score to include a product in results


def _get_intent_multiplier(product: Dict[str, Any], query_lower: str) -> float:
    """Return the highest applicable boost multiplier for a product given the query."""
    multiplier = 1.0
    product_text = f"{product.get('name', '')} {product.get('description', '')} {' '.join(product.get('tags', []))}".lower()

    for intent_keyword, tag_boosts in INTENT_BOOSTS.items():
        if intent_keyword in query_lower:
            for tag, boost in tag_boosts.items():
                if tag in product_text:
                    multiplier = max(multiplier, boost)
    return multiplier


def rank_products_by_query(
    query: str,
    products: List[Dict[str, Any]],
    threshold: float = SIMILARITY_THRESHOLD,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Rank products by semantic similarity + intent boost.

    Returns a list of product dicts with `_score` added, sorted descending.
    Products below `threshold` are excluded.
    """
    if not SEMANTIC_AVAILABLE or not products:
        return _keyword_fallback(query, products)

    # 1. Encode + normalize query
    model = get_model()
    query_vec = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)

    query_lower = query.lower()
    scored = []

    for p in products:
        emb = p.get("embedding")
        if not emb:
            base_score = 0.0
        else:
            # Fast dot-product (equivalent to cosine since both are L2-normalized)
            product_vec = np.array(emb, dtype=np.float32)
            # Re-normalize stored embedding in case old ones weren't normalized
            norm = np.linalg.norm(product_vec)
            if norm > 0:
                product_vec = product_vec / norm
            base_score = float(np.dot(query_vec, product_vec))

        # 2. Apply intent boost
        boost = _get_intent_multiplier(p, query_lower)
        final_score = base_score * boost

        if final_score >= threshold:
            scored.append({**p, "_score": round(final_score, 4)})

    # 3. Sort by score descending
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:limit]


def _keyword_fallback(query: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Simple keyword-based fallback when sentence-transformers is unavailable."""
    q = query.lower()
    def score(p):
        text = f"{p.get('name','')} {p.get('description','')} {' '.join(p.get('tags',[]))}".lower()
        return sum(1 for word in q.split() if word in text)
    return sorted(products, key=score, reverse=True)
