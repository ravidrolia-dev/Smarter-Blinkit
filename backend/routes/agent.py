from fastapi import APIRouter, Query, Header
from services.recipe_agent import parse_recipe_ingredients, find_ingredients_from_db
from services.jwt_utils import decode_token
from typing import Optional

router = APIRouter()

@router.get("/recipe")
async def recipe_agent(
    meal: str = Query(..., description="Natural language meal request, e.g. 'Make Pizza'"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Demand-Driven Recipe Agent:
    1. Parse recipe (AI or Cache)
    2. Check DB for availability
    3. Record demand for missing items
    """
    # Try to get user_id from token for demand tracking
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub")

    # Step 1: Get Structured Recipe
    recipe = await parse_recipe_ingredients(meal)
    if not recipe:
        return {
            "success": False,
            "message": "Recipe generation is temporarily unavailable. Please try again later."
        }

    # Step 2: Match ingredients with DB & Record Demand
    ingredients = recipe.get("ingredients", [])
    ingredient_results = await find_ingredients_from_db(ingredients, user_id=user_id, lat=lat, lng=lng)

    available = [r for r in ingredient_results if r["found"]]
    out_of_stock = [r for r in ingredient_results if not r["found"]]

    return {
        "success": True,
        "recipe_name": recipe.get("recipe_name", meal.title()),
        "instructions": recipe.get("instructions", []),
        "available": available,
        "out_of_stock": out_of_stock,
        "total_items": len(ingredient_results)
    }
