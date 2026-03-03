from fastapi import APIRouter, Query
from services.recipe_agent import parse_recipe_ingredients, find_ingredients_from_db
from typing import Optional

router = APIRouter()

@router.get("/recipe")
async def recipe_agent(
    meal: str = Query(..., description="Natural language meal request, e.g. 'Make Pizza for 4 people'"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None)
):
    """
    AI Recipe Agent — parses a meal request and finds all ingredients from nearby shops.
    """
    # Step 1: Parse ingredients from meal description using Gemini
    ingredients = await parse_recipe_ingredients(meal)

    # Step 2: Find ingredients from nearby inventory
    results = await find_ingredients_from_db(ingredients, lat, lng)

    found = [r for r in results if r["found"]]
    not_found = [r for r in results if not r["found"]]

    return {
        "meal": meal,
        "ingredients_parsed": len(ingredients),
        "found": found,
        "not_found": not_found,
        "cart_ready": len(not_found) == 0,
        "total_items": len(results)
    }
