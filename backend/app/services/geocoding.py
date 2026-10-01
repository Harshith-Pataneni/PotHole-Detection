"""
Reverse Geocoding Service
=========================
Converts latitude and longitude into human-readable road addresses
using OpenStreetMap Nominatim (Free, keyless, with rate-limiting respect).
"""

from typing import Optional
import httpx
from app.config import settings
from app.core.logging import logger


class GeocodingService:
    @staticmethod
    async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
        if not settings.REVERSE_GEOCODING_ENABLED:
            return None

        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "zoom": 16,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "PotholeReportingPlatform/1.0 (civic-tech-edu)"
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    display_name = data.get("display_name")
                    # If display name is very long, extract road + city
                    address = data.get("address", {})
                    road = address.get("road") or address.get("street") or address.get("suburb")
                    city = address.get("city") or address.get("town") or address.get("village")
                    if road and city:
                        return f"{road}, {city}"
                    return display_name[:120] if display_name else None
        except Exception as e:
            logger.debug(f"Reverse geocoding lookup failed (non-critical): {e}")

        return None


geocoding_service = GeocodingService()
