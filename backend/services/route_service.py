import httpx
import os
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RouteService:
    def __init__(self):
        # Support both env var naming conventions; prefer the canonical one
        self.api_key = (
            os.getenv("OPENROUTESERVICE_API_KEY")
            or os.getenv("OPENROUTE_SERVICE_API_KEY")
        )
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    async def get_route_metrics(self, coordinates: List[List[float]]) -> Optional[Dict[str, Any]]:
        """
        coordinates: List of [lng, lat] pairs.
        Returns {distance_km, duration_min, geometry} or None.
        """
        if len(coordinates) < 2:
            return {"distance_km": 0, "duration_min": 0}

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "coordinates": coordinates
        }

        try:
            async with httpx.AsyncClient() as client:
                # OpenRouteService expects POST for v2 directions
                response = await client.post(self.base_url, json=payload, headers=headers, timeout=15.0)
                
                if response.status_code == 403:
                    logger.warning("OpenRouteService API key invalid or quota exceeded. Falling back to mock/Haversine.")
                    return None

                response.raise_for_status()
                data = response.json()
                
                # Extract distance and duration from summary
                # summary is usually in features[0].properties.summary
                summary = data["routes"][0]["summary"]
                distance_m = summary["distance"]
                duration_s = summary["duration"]
                geometry = data["routes"][0].get("geometry")

                return {
                    "distance_km": round(distance_m / 1000, 2),
                    "duration_min": round(duration_s / 60),
                    "geometry": geometry
                }
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return None

    async def get_optimized_route(self, coordinates: List[List[float]]) -> Optional[Dict[str, Any]]:
        """
        High-level entry point for delivery route optimization.

        Input: coordinates as list of [lng, lat] pairs
          e.g. [[shop1_lng, shop1_lat], [shop2_lng, shop2_lat], [buyer_lng, buyer_lat]]

        Returns:
          {
            total_distance_km: float,
            total_duration_minutes: float,
            route_order: list   # same coordinate list, in traversal order
          }
        or None on failure.
        """
        metrics = await self.get_route_metrics(coordinates)
        if metrics:
            return {
                "total_distance_km": metrics["distance_km"],
                "total_duration_minutes": metrics["duration_min"],
                "route_order": coordinates,
                "geometry": metrics.get("geometry")
            }
        return None


# Singleton instance
route_service = RouteService()
