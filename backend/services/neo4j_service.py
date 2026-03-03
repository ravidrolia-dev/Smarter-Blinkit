from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            _driver.verify_connectivity()
            print("✅ Neo4j connected")
        except Exception as e:
            print(f"⚠️ Neo4j connection failed (recommendations disabled): {e}")
            _driver = None
    return _driver

def create_product_node(product_id: str, name: str, category: str, tags: list):
    """Create or merge a product node in Neo4j."""
    driver = get_driver()
    if not driver:
        return
    with driver.session() as session:
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
    with driver.session() as session:
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
    with driver.session() as session:
        session.run(
            """
            MATCH (a:Product {id: $id1}), (b:Product {id: $id2})
            MERGE (a)-[r:SIMILAR_TO]-(b)
            SET r.score = $score
            """,
            id1=product_id_1, id2=product_id_2, score=score
        )

def get_recommendations(product_id: str, limit: int = 6) -> List[Dict]:
    """Fetch BOUGHT_WITH and SIMILAR_TO recommendations for a product."""
    driver = get_driver()
    if not driver:
        return []
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {id: $id})-[r:BOUGHT_WITH|SIMILAR_TO]-(rec:Product)
            RETURN rec.id AS id, rec.name AS name, type(r) AS rel_type,
                   CASE type(r) WHEN 'BOUGHT_WITH' THEN r.count ELSE r.score END AS strength
            ORDER BY strength DESC
            LIMIT $limit
            """,
            id=product_id, limit=limit
        )
        return [dict(record) for record in result]

def record_order_purchase(product_ids: List[str]):
    """After an order, create BOUGHT_WITH links for all product pairs in the order."""
    for i in range(len(product_ids)):
        for j in range(i + 1, len(product_ids)):
            create_bought_with(product_ids[i], product_ids[j])
