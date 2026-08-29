"""
Overpass Service — Phase 5 Hyper-Local Market Intelligence.

Queries the Overpass API (OpenStreetMap data) to retrieve nearby POIs,
shops, amenities, and businesses.

Design principles:
  - All HTTP calls are isolated in `_overpass_query()` so tests can mock them
  - Raw Overpass responses are normalised into clean NearbyPlace dataclasses
  - Failures / timeouts return empty lists rather than crashing

Public Overpass endpoints used (no API key required):
  https://overpass-api.de/api/interpreter
  (Mirror: https://overpass.kumi.systems/api/interpreter)
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import httpx

from app.services.location_service import haversine_distance, validate_coordinates

# ── Constants ──────────────────────────────────────────────────────────────────

OVERPASS_URL      = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT  = 25.0      # seconds — Overpass can be slow
MAX_RADIUS_KM     = 15.0      # hard ceiling to prevent huge queries
ALLOWED_RADII_KM  = {1, 2, 5, 10}
DEFAULT_RADIUS_KM = 5


# ── OSM tag → RuralBiz category mapping ───────────────────────────────────────

#: Maps an (OSM key, OSM value) pair to a human-readable RuralBiz category.
#: The first match wins, so order matters (specific before general).
OSM_CATEGORY_MAP: List[Tuple[str, str, str]] = [
    # (key, value, ruralbiz_category)
    ("shop",     "dairy",          "Dairy & Milk"),
    ("shop",     "milk",           "Dairy & Milk"),
    ("shop",     "farm",           "Agriculture"),
    ("shop",     "agrarian",       "Agriculture"),
    ("shop",     "garden_centre",  "Agriculture"),
    ("shop",     "butcher",        "Meat & Poultry"),
    ("shop",     "fishmonger",     "Fish & Seafood"),
    ("shop",     "clothes",        "Tailoring & Clothing"),
    ("shop",     "tailor",         "Tailoring & Clothing"),
    ("craft",    "tailor",         "Tailoring & Clothing"),
    ("shop",     "fabric",         "Tailoring & Clothing"),
    ("shop",     "shoes",          "Footwear"),
    ("shop",     "bakery",         "Food Production"),
    ("shop",     "pastry",         "Food Production"),
    ("shop",     "confectionery",  "Food Production"),
    ("shop",     "supermarket",    "Retail & Distribution"),
    ("shop",     "convenience",    "Retail & Distribution"),
    ("shop",     "kiosk",          "Retail & Distribution"),
    ("shop",     "general",        "Retail & Distribution"),
    ("shop",     "grocery",        "Retail & Distribution"),
    ("amenity",  "marketplace",    "Market"),
    ("amenity",  "market",         "Market"),
    ("amenity",  "pharmacy",       "Medical & Health"),
    ("amenity",  "clinic",         "Medical & Health"),
    ("amenity",  "doctors",        "Medical & Health"),
    ("amenity",  "hospital",       "Medical & Health"),
    ("amenity",  "veterinary",     "Veterinary & Animal Care"),
    ("amenity",  "restaurant",     "Food Service"),
    ("amenity",  "fast_food",      "Food Service"),
    ("amenity",  "food_court",     "Food Service"),
    ("amenity",  "cafe",           "Tea & Coffee Shop"),
    ("amenity",  "tea",            "Tea & Coffee Shop"),
    ("amenity",  "fuel",           "Energy & Fuel"),
    ("amenity",  "bank",           "Banking & Finance"),
    ("amenity",  "atm",            "Banking & Finance"),
    ("amenity",  "school",         "Education"),
    ("amenity",  "college",        "Education"),
    ("amenity",  "bus_station",    "Transport"),
    ("amenity",  "bus_stop",       "Transport"),
    ("shop",     "hardware",       "Hardware & Tools"),
    ("shop",     "electronics",    "Electronics"),
    ("shop",     "mobile_phone",   "Electronics"),
    ("shop",     "beauty",         "Beauty & Wellness"),
    ("shop",     "hairdresser",    "Beauty & Wellness"),
    ("shop",     "optician",       "Optical"),
    ("shop",     "florist",        "Horticulture"),
    ("shop",     "photo",          "Photography"),
    ("craft",    "pottery",        "Handicrafts"),
    ("craft",    "jeweller",       "Jewellery"),
    ("shop",     "jewelry",        "Jewellery"),
    # Fallback generics
    ("shop",     "*",              "Retail"),
    ("amenity",  "*",              "Amenity"),
    ("craft",    "*",              "Craft / Workshop"),
    ("office",   "*",              "Office / Services"),
]


# ─── Business-name → relevant OSM tags mapping ────────────────────────────────
# Used to find *direct* competitors for a given RuralBiz catalog business.
# Each entry maps a lowercase keyword from business.name to a list of
# (osm_key, osm_value) pairs that represent that type of establishment.

BUSINESS_OSM_MAPPING: Dict[str, List[Tuple[str, str]]] = {
    # Dairy / Milk
    "dairy":       [("shop", "dairy"), ("shop", "milk"), ("shop", "farm")],
    "milk":        [("shop", "dairy"), ("shop", "milk")],
    # Tailoring
    "tailor":      [("shop", "tailor"), ("shop", "clothes"), ("craft", "tailor"), ("shop", "fabric")],
    "tailoring":   [("shop", "tailor"), ("shop", "clothes"), ("craft", "tailor")],
    "boutique":    [("shop", "clothes"), ("shop", "tailor")],
    "clothes":     [("shop", "clothes"), ("shop", "tailor")],
    "clothing":    [("shop", "clothes"), ("shop", "tailor")],
    "garment":     [("shop", "clothes"), ("craft", "tailor")],
    # Grocery / Kirana
    "kirana":      [("shop", "convenience"), ("shop", "general"), ("shop", "grocery"), ("shop", "supermarket")],
    "grocery":     [("shop", "grocery"), ("shop", "convenience"), ("shop", "supermarket")],
    "general":     [("shop", "general"), ("shop", "convenience")],
    "retail":      [("shop", "general"), ("shop", "convenience"), ("shop", "supermarket"), ("shop", "kiosk")],
    "supermarket": [("shop", "supermarket"), ("shop", "grocery"), ("shop", "convenience")],
    # Bakery / Food Production
    "bakery":      [("shop", "bakery"), ("shop", "pastry"), ("shop", "confectionery")],
    "food":        [("amenity", "restaurant"), ("amenity", "fast_food"), ("shop", "bakery"), ("shop", "grocery")],
    # Tea / Café
    "tea":         [("amenity", "cafe"), ("amenity", "tea"), ("amenity", "fast_food")],
    "café":        [("amenity", "cafe"), ("amenity", "tea")],
    "cafe":        [("amenity", "cafe"), ("amenity", "tea")],
    "snack":       [("amenity", "fast_food"), ("amenity", "cafe")],
    # Medical
    "medical":     [("amenity", "pharmacy"), ("amenity", "clinic"), ("amenity", "doctors")],
    "pharmacy":    [("amenity", "pharmacy")],
    "clinic":      [("amenity", "clinic"), ("amenity", "doctors"), ("amenity", "hospital")],
    "health":      [("amenity", "pharmacy"), ("amenity", "clinic")],
    # Agriculture
    "agriculture": [("shop", "agrarian"), ("shop", "farm"), ("shop", "garden_centre")],
    "farming":     [("shop", "agrarian"), ("shop", "farm")],
    "poultry":     [("shop", "butcher"), ("shop", "farm")],
    # Handicrafts
    "handicraft":  [("craft", "pottery"), ("craft", "tailor"), ("craft", "jeweller")],
    "craft":       [("craft", "pottery"), ("craft", "tailor"), ("craft", "jeweller")],
    "pottery":     [("craft", "pottery")],
    # Beauty
    "beauty":      [("shop", "beauty"), ("shop", "hairdresser")],
    "salon":       [("shop", "beauty"), ("shop", "hairdresser")],
    "barber":      [("shop", "hairdresser")],
    # Electronics
    "electronics": [("shop", "electronics"), ("shop", "mobile_phone")],
    "mobile":      [("shop", "mobile_phone")],
    # Fertilizer / Agri-input
    "fertilizer":  [("shop", "agrarian")],
    "agri":        [("shop", "agrarian"), ("shop", "farm")],
    # Hardware
    "hardware":    [("shop", "hardware")],
    # Education
    "tuition":     [("amenity", "school"), ("amenity", "college")],
    "coaching":    [("amenity", "school")],
    # Fuel
    "fuel":        [("amenity", "fuel")],
    "petrol":      [("amenity", "fuel")],
}


# ── Data containers ────────────────────────────────────────────────────────────

@dataclass
class NearbyPlace:
    osm_id:          str
    name:            str
    category:        str           # RuralBiz category (normalised)
    osm_tags:        Dict[str, str]
    latitude:        float
    longitude:       float
    distance_meters: float


@dataclass
class OverpassResult:
    places:        List[NearbyPlace] = field(default_factory=list)
    error:         Optional[str]    = None
    from_cache:    bool             = False
    query_time_ms: float            = 0.0


# ── Simple in-process cache ────────────────────────────────────────────────────
# TTL-based dict cache keyed by (lat_rounded, lon_rounded, radius_km, query_hash).
# Good enough for the current project scale.

_cache: Dict[str, Tuple[float, OverpassResult]] = {}  # key → (expires_at, result)
CACHE_TTL_SECONDS = 600   # 10 minutes


def _cache_key(lat: float, lon: float, radius_km: float, query: str) -> str:
    # Round coords to 3 dp (~110 m precision) to improve cache hit rate
    return f"{lat:.3f},{lon:.3f},{radius_km},{hash(query)}"


def _cache_get(key: str) -> Optional[OverpassResult]:
    entry = _cache.get(key)
    if entry and time.time() < entry[0]:
        result = entry[1]
        result.from_cache = True
        return result
    if key in _cache:
        del _cache[key]
    return None


def _cache_set(key: str, result: OverpassResult) -> None:
    try:
        _cache[key] = (time.time() + CACHE_TTL_SECONDS, result)
    except Exception:
        pass   # cache write failures are silently ignored


# ── OSM tag normalisation ──────────────────────────────────────────────────────

def _classify_osm_tags(tags: Dict[str, str]) -> str:
    """Map OSM tags to a RuralBiz category string."""
    for key, value, category in OSM_CATEGORY_MAP:
        if value == "*":
            if key in tags:
                return category
        else:
            if tags.get(key) == value:
                return category
    return "Other"


def _extract_name(tags: Dict[str, str]) -> str:
    return (
        tags.get("name")
        or tags.get("name:en")
        or tags.get("brand")
        or tags.get("operator")
        or "Unnamed"
    )


def _element_to_place(element: dict, center_lat: float, center_lon: float) -> Optional[NearbyPlace]:
    """Convert a raw Overpass element into a NearbyPlace. Returns None if unusable."""
    try:
        tags = element.get("tags", {})
        if not tags:
            return None

        # Get coordinates — nodes have lat/lon directly; ways/relations have center
        if element["type"] == "node":
            lat = float(element["lat"])
            lon = float(element["lon"])
        else:
            c = element.get("center", {})
            if not c:
                return None
            lat = float(c["lat"])
            lon = float(c["lon"])

        name     = _extract_name(tags)
        category = _classify_osm_tags(tags)
        dist     = haversine_distance(center_lat, center_lon, lat, lon)

        return NearbyPlace(
            osm_id          = f"{element['type']}/{element['id']}",
            name            = name,
            category        = category,
            osm_tags        = tags,
            latitude        = lat,
            longitude       = lon,
            distance_meters = round(dist, 1),
        )
    except Exception:
        return None


# ── HTTP helper (isolated for testability) ────────────────────────────────────

async def _overpass_query(overpass_ql: str) -> dict:
    """Execute a raw Overpass QL query. Returns parsed JSON or raises."""
    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT) as client:
        resp = await client.post(
            OVERPASS_URL,
            content=overpass_ql,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


# ── Overpass QL builder ───────────────────────────────────────────────────────

def _build_overpass_query(lat: float, lon: float, radius_m: float, tag_filters: List[str]) -> str:
    """
    Build an Overpass QL query for the given location, radius, and tag filters.

    tag_filters items look like:  'node["shop"="dairy"]' or 'node["amenity"]'
    The query fetches nodes, ways, and relations and requests center coordinates
    for ways/relations.
    """
    union_parts = []
    for tf in tag_filters:
        # tf example: '["shop"="dairy"]'
        union_parts.append(f'node{tf}(around:{radius_m:.0f},{lat},{lon});')
        union_parts.append(f'way{tf}(around:{radius_m:.0f},{lat},{lon});')
        union_parts.append(f'relation{tf}(around:{radius_m:.0f},{lat},{lon});')

    union = "\n".join(union_parts)
    return f"""
[out:json][timeout:20];
(
{union}
);
out center tags;
""".strip()


def _build_general_query(lat: float, lon: float, radius_m: float) -> str:
    """Build a broad query for all shops, amenities, and crafts in the radius."""
    tag_filters = ['["shop"]', '["amenity"~"restaurant|fast_food|cafe|pharmacy|clinic|marketplace|bank"]', '["craft"]']
    return _build_overpass_query(lat, lon, radius_m, tag_filters)


def _competitor_tag_filters(business_name: str) -> List[str]:
    """
    Return Overpass tag-filter strings for the direct competitors of a given
    business name.  Uses keyword matching against BUSINESS_OSM_MAPPING.
    """
    name_lower = business_name.lower()
    matched_pairs: List[Tuple[str, str]] = []
    seen: set = set()

    for keyword, pairs in BUSINESS_OSM_MAPPING.items():
        if keyword in name_lower:
            for pair in pairs:
                if pair not in seen:
                    seen.add(pair)
                    matched_pairs.append(pair)

    if not matched_pairs:
        return []

    filters = []
    for key, val in matched_pairs:
        filters.append(f'["{key}"="{val}"]')
    return filters


# ── Public API ────────────────────────────────────────────────────────────────

def _validate_radius(radius_km: float) -> float:
    """Clamp radius to allowed range and return metres."""
    radius_km = max(1.0, min(radius_km, MAX_RADIUS_KM))
    return radius_km * 1000.0


async def fetch_nearby_places(
    lat:       float,
    lon:       float,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> OverpassResult:
    """
    Fetch all nearby shops, amenities, and crafts within the given radius.
    Results are cached for CACHE_TTL_SECONDS.
    """
    validate_coordinates(lat, lon)
    radius_m = _validate_radius(radius_km)

    query    = _build_general_query(lat, lon, radius_m)
    cache_k  = _cache_key(lat, lon, radius_km, "general")

    cached = _cache_get(cache_k)
    if cached:
        return cached

    t0 = time.time()
    try:
        data   = await _overpass_query(query)
        places = [
            p for e in data.get("elements", [])
            if (p := _element_to_place(e, lat, lon)) is not None
        ]
        result = OverpassResult(
            places        = places,
            query_time_ms = (time.time() - t0) * 1000,
        )
    except httpx.TimeoutException:
        result = OverpassResult(error="Overpass API timed out. Please try again.")
    except Exception as exc:
        result = OverpassResult(error=f"Overpass API error: {str(exc)[:120]}")

    _cache_set(cache_k, result)
    return result


async def fetch_competitors(
    lat:           float,
    lon:           float,
    business_name: str,
    radius_km:     float = DEFAULT_RADIUS_KM,
) -> OverpassResult:
    """
    Fetch POIs that are direct competitors for the given business name.
    Returns an OverpassResult with only competitor places.
    """
    validate_coordinates(lat, lon)
    radius_m = _validate_radius(radius_km)
    filters  = _competitor_tag_filters(business_name)

    if not filters:
        # No OSM mapping found for this business — return empty
        return OverpassResult(places=[], error=None)

    query   = _build_overpass_query(lat, lon, radius_m, filters)
    cache_k = _cache_key(lat, lon, radius_km, f"competitor:{business_name.lower()}")

    cached = _cache_get(cache_k)
    if cached:
        return cached

    t0 = time.time()
    try:
        data   = await _overpass_query(query)
        places = [
            p for e in data.get("elements", [])
            if (p := _element_to_place(e, lat, lon)) is not None
        ]
        result = OverpassResult(
            places        = places,
            query_time_ms = (time.time() - t0) * 1000,
        )
    except httpx.TimeoutException:
        result = OverpassResult(error="Overpass API timed out while fetching competitors.")
    except Exception as exc:
        result = OverpassResult(error=f"Overpass API error: {str(exc)[:120]}")

    _cache_set(cache_k, result)
    return result


def clear_cache() -> None:
    """Clear the in-process cache. Primarily for testing."""
    global _cache
    _cache = {}
