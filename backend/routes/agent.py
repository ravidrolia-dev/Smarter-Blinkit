from fastapi import APIRouter, Query
from services.recipe_agent import parse_recipe_ingredients, find_ingredients_from_db, DEFAULT_MODEL
from typing import Optional

router = APIRouter()

@router.get("/recipe")
async def recipe_agent(
    meal: str = Query(..., description="Natural language meal request, e.g. 'Make Pizza for 4 people'"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    model: str = Query(DEFAULT_MODEL, description="Gemini model to use: gemini-1.5-flash or gemini-2.5-flash"),
):
    """
    AI Recipe Agent — parses a meal request and finds all ingredients from nearby shops.
    """
    # Step 1: Parse ingredients from meal description using Gemini
    ingredients = await parse_recipe_ingredients(meal, model_name=model)

    # Step 2: Find ingredients from nearby inventory
    results = await find_ingredients_from_db(ingredients, lat, lng)

    found = [r for r in results if r["found"]]
    not_found = [r for r in results if not r["found"]]

    return {
        "meal": meal,
        "model_used": model,
        "ingredients_parsed": len(ingredients),
        "found": found,
        "not_found": not_found,
        "cart_ready": len(not_found) == 0,
        "total_items": len(results)
    }
