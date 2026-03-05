try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("neo4j package not installed - graph recommendations disabled")
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

_driver = None

def get_driver():
    global _driver
    if not NEO4J_AVAILABLE:
        return None
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            _driver.verify_connectivity()
            print("Neo4j connected")
        except Exception as e:
            print(f"Neo4j connection failed (recommendations disabled): {e}")
            _driver = None
    return _driver

def create_product_node(product_id: str, name: str, category: str, tags: list):
    """Create or merge a product node in Neo4j."""
    driver = get_driver()
    if not driver:
        return
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            MERGE (p:Product {id: $id})
            SET p.name = $name, p.category = $category, p.tags = $tags
            """,
            id=product_id, name=name, category=category, tags=tags
        )

def create_bought_with(product_id_1: str, product_id_2: str):
    """Create or increment BOUGHT_WITH relationship between two products."""
    driver = get_driver()
    if not driver:
        return
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            MATCH (a:Product {id: $id1}), (b:Product {id: $id2})
            MERGE (a)-[r:BOUGHT_WITH]-(b)
            ON CREATE SET r.count = 1
            ON MATCH SET r.count = r.count + 1
            """,
            id1=product_id_1, id2=product_id_2
        )

def create_similar_to(product_id_1: str, product_id_2: str, score: float = 1.0):
    """Create SIMILAR_TO relationship."""
    driver = get_driver()
    if not driver:
        return
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            MATCH (a:Product {id: $id1}), (b:Product {id: $id2})
            MERGE (a)-[r:SIMILAR_TO]-(b)
            SET r.score = $score
            """,
            id1=product_id_1, id2=product_id_2, score=score
        )

def get_recommendations(product_id: str, limit: int = 10) -> Dict[str, List[str]]:
    """Fetch BOUGHT_WITH and SIMILAR_TO recommendations, separated by type."""
    driver = get_driver()
    if not driver:
        return {"similar": [], "bought_with": []}
    
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(
                """
                MATCH (p:Product {id: $id})
                MATCH (p)-[r:BOUGHT_WITH|SIMILAR_TO]-(rec:Product)
                WHERE rec.id <> $id AND rec.name <> p.name
                RETURN rec.id AS id, type(r) AS rel_type,
                       CASE type(r) WHEN 'BOUGHT_WITH' THEN r.count ELSE r.score END AS strength
                ORDER BY strength DESC
                LIMIT $limit
                """,
                id=product_id, limit=limit
            )
            
            recs = {"similar": [], "bought_with": []}
            for record in result:
                if record["rel_type"] == "SIMILAR_TO":
                    recs["similar"].append(record["id"])
                else:
                    recs["bought_with"].append(record["id"])
            return recs
    except Exception as e:
        print(f"Neo4j recommendation fetch failed: {e}")
        return {"similar": [], "bought_with": []}

async def sync_similar_products(product_id: str, name: str, category: str, embedding: List[float]):
    """
    Automated similarity linking.
    1. Links products in the same category.
    2. Links products with high semantic similarity (using MongoDB vector search or manual comparison).
    Note: For simplicity here, we link to other products in the same category.
    """
    from database import get_products_collection
    from bson import ObjectId
    import numpy as np
    
    driver = get_driver()
    if not driver:
        return

    products_col = get_products_collection()
    # Find up to 10 other products in same category to link
    cursor = products_col.find({
        "category": category,
        "_id": {"$ne": ObjectId(product_id)}
    }).limit(10)
    
    other_products = await cursor.to_list(length=10)
    
    with driver.session(database=NEO4J_DATABASE) as session:
        for other in other_products:
            other_id = str(other["_id"])
            # Skip if it's the same product name (duplicate entries in DB)
            if other.get("name") == name:
                continue
                
            score = 0.5 # Base score for same category
            
            # If both have embeddings, calculate cosine similarity
            other_emb = other.get("embedding")
            if embedding and other_emb:
                v1 = np.array(embedding)
                v2 = np.array(other_emb)
                # Both are normalized in our system, so dot product = cosine similarity
                score = float(np.dot(v1, v2))
            
            if score > 0.4: # Only link if similarity is decent
                session.run(
                    """
                    MATCH (a:Product {id: $id1}), (b:Product {id: $id2})
                    MERGE (a)-[r:SIMILAR_TO]-(b)
                    SET r.score = $score
                    """,
                    id1=product_id, id2=other_id, score=score
                )

def record_order_purchase(product_ids: List[str]):
    """After an order, create BOUGHT_WITH links for all product pairs in the order."""
    driver = get_driver()
    if not driver: return
    
    for i in range(len(product_ids)):
        for j in range(i + 1, len(product_ids)):
            try:
                create_bought_with(product_ids[i], product_ids[j])
            except Exception: pass
