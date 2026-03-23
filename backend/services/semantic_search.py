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

# ── Model setup ──────────────────────────────────────────────────────────────
SEMANTIC_AVAILABLE = False # Disabled for memory optimization (Render 512MB)

def embed_text(text: str) -> List[float]:
    """Placeholder for text embedding. Returns empty list as models are disabled."""
    return []


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
    Rank products by keyword relevance + intent boost.
    Optimized for memory by removing sentence-transformers.
    """
    return _keyword_fallback(query, products)[:limit]


def _keyword_fallback(query: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Simple keyword-based relevance ranking with intent boosting."""
    q = query.lower()
    q_words = q.split()
    
    scored = []
    for p in products:
        text = f"{p.get('name','') or ''} {p.get('description','') or ''} {' '.join(p.get('tags',[]))}".lower()
        
        # Base score = word overlap count normalized by query length
        matches = sum(2 for word in q_words if word in text) # exact word in text
        # also check partial matches
        partial_matches = sum(0.5 for word in q_words if word in text and word not in text.split())
        
        base_score = (matches + partial_matches) / (len(q_words) or 1)
        
        # Apply intent boost
        boost = _get_intent_multiplier(p, q)
        final_score = base_score * boost
        
        # We need to add _score for compatibility with routes
        p_with_score = {**p, "_score": round(final_score, 4)}
        scored.append(p_with_score)
        
    # Sort by score descending
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored
