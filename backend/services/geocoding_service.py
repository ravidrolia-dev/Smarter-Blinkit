import httpx
import asyncio
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Smarter-Blinkit/1.0"
        }
        self.cache = {} # Simple in-memory cache

    async def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address string to (latitude, longitude).
        Returns None if not found.
        """
        if not address:
            return None
            
        # Check cache
        clean_addr = address.strip().lower()
        if clean_addr in self.cache:
            return self.cache[clean_addr]

        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.base_url, params=params, headers=self.headers, timeout=10.0)
                    
                    if response.status_code == 429:
                        wait = (attempt + 1) * 1.5
                        logger.warning(f"Nominatim Rate Limit. Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                        
                    response.raise_for_status()
                    data = response.json()
                    
                    if data and len(data) > 0:
                        lat = float(data[0]["lat"])
                        lng = float(data[0]["lon"])
                        self.cache[clean_addr] = (lat, lng)
                        return lat, lng
                    
                    return None
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Geocoding error for address '{address}': {e}")
                    return None
                await asyncio.sleep(1.0)
        return None

# Singleton instance
geocoding_service = GeocodingService()


async def geocode_address(address: str) -> Optional[dict]:
    """
    Convenience function: convert a text address to {"lat": float, "lng": float}.
    Uses Nominatim (OpenStreetMap). Returns None if address cannot be resolved.

    Example:
        coords = await geocode_address("MNIT Jaipur")
        # {"lat": 26.8544, "lng": 75.8022}
    """
    coords = await geocoding_service.get_coordinates(address)
    if coords:
        return {"lat": coords[0], "lng": coords[1]}
    return None
