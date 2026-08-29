"""
Location Service — Phase 5 Hyper-Local Market Intelligence.

Handles:
  - Coordinate validation
  - Location text search via Nominatim (OpenStreetMap-compatible, free)
  - Reverse geocoding
  - Distance calculations

External HTTP calls are isolated into small async helper functions so they can
be easily mocked in unit tests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

import httpx

# ── Constants ──────────────────────────────────────────────────────────────────

# Nominatim — free OpenStreetMap geocoding (no API key required)
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

# User-Agent required by Nominatim ToS
NOMINATIM_HEADERS = {
    "User-Agent": "RuralBizAI/1.0 (educational planning tool; contact: ruralbiz@example.com)"
}

# Request timeout in seconds
REQUEST_TIMEOUT = 10.0


# ── Data containers ────────────────────────────────────────────────────────────

@dataclass
class LocationResult:
    display_name: str
    latitude:     float
    longitude:    float
    place_id:     Optional[str] = None
    osm_type:     Optional[str] = None
    country:      Optional[str] = None
    state:        Optional[str] = None
    district:     Optional[str] = None


# ── Coordinate helpers ─────────────────────────────────────────────────────────

def validate_coordinates(lat: float, lon: float) -> None:
    """Raise ValueError if lat/lon are out of valid range."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in **meters** between two lat/lon points.
    Uses the Haversine formula.
    """
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def radius_km_to_degrees(radius_km: float, latitude: float) -> float:
    """Approximate degree-radius for a given km radius at a given latitude."""
    lat_deg = radius_km / 111.0
    lon_deg = radius_km / (111.0 * math.cos(math.radians(latitude)))
    return max(lat_deg, lon_deg)


# ── HTTP helpers (isolated for testability) ────────────────────────────────────

async def _nominatim_search(query: str, limit: int = 5) -> list:
    """Call Nominatim search API. Returns raw JSON list."""
    params = {
        "q":              query,
        "format":         "jsonv2",
        "limit":          limit,
        "addressdetails": 1,
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            f"{NOMINATIM_BASE_URL}/search",
            params=params,
            headers=NOMINATIM_HEADERS,
        )
        response.raise_for_status()
        return response.json()


async def _nominatim_reverse(lat: float, lon: float) -> dict:
    """Reverse-geocode a lat/lon pair via Nominatim."""
    params = {
        "lat":    lat,
        "lon":    lon,
        "format": "jsonv2",
        "zoom":   10,
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            f"{NOMINATIM_BASE_URL}/reverse",
            params=params,
            headers=NOMINATIM_HEADERS,
        )
        response.raise_for_status()
        return response.json()


# ── Public API ────────────────────────────────────────────────────────────────

def _parse_nominatim_result(item: dict) -> LocationResult:
    address = item.get("address", {})
    return LocationResult(
        display_name = item.get("display_name", ""),
        latitude     = float(item.get("lat", 0)),
        longitude    = float(item.get("lon", 0)),
        place_id     = str(item.get("place_id", "")),
        osm_type     = item.get("osm_type"),
        country      = address.get("country"),
        state        = address.get("state"),
        district     = address.get("county") or address.get("district"),
    )


async def search_location(query: str, limit: int = 5) -> List[LocationResult]:
    """
    Search for a location by name.

    Returns a list of matching LocationResult objects (may be empty).
    Network / API errors are caught and return an empty list so the caller
    can present a graceful 'no results' message.
    """
    if not query or len(query.strip()) < 2:
        return []
    try:
        raw = await _nominatim_search(query.strip(), limit=limit)
        return [_parse_nominatim_result(item) for item in raw]
    except Exception:
        return []


async def reverse_geocode(lat: float, lon: float) -> Optional[LocationResult]:
    """
    Reverse-geocode coordinates into a human-readable location.
    Returns None on any error.
    """
    try:
        validate_coordinates(lat, lon)
        raw = await _nominatim_reverse(lat, lon)
        if "error" in raw:
            return None
        return _parse_nominatim_result(raw)
    except Exception:
        return None
