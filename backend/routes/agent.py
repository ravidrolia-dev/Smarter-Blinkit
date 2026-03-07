from fastapi import APIRouter, Query
from services.recipe_agent import parse_recipe_ingredients, find_ingredients_from_db
from typing import Optional

router = APIRouter()

@router.get("/recipe")
async def recipe_agent(
    meal: str = Query(..., description="Natural language meal request, e.g. 'Make Pizza'"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
):
    """
    AI Recipe Agent (V4) — parses a meal request and finds all ingredients efficiently.
    """
    # Step 1: Parse ingredients (Batch)
    parse_res = await parse_recipe_ingredients(meal)
    ingredients = parse_res.get("ingredients", [])
    parse_warning = parse_res.get("warning")

    # Step 2: Find ingredients from inventory (Quota-protected)
    db_res = await find_ingredients_from_db(ingredients, lat, lng)
    results = db_res.get("results", [])
    meta = db_res.get("meta", {})

    found = [r for r in results if r["found"]]
    not_found = [r for r in results if not r["found"]]

    return {
        "meal": meal,
        "ingredients_parsed": len(ingredients),
        "found": found,
        "not_found": not_found,
        "cart_ready": len(not_found) == 0 and not meta.get("partial"),
        "total_items": len(results),
        "warning": parse_warning or meta.get("message")
    }
