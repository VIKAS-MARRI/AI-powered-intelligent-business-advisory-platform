"""
Market Intelligence API endpoints — Phase 5.

GET  /locations/search?q=          — search for a location by name
POST /market/analyze               — full market + competitor analysis
POST /market/nearby                — nearby businesses only

All endpoints require JWT authentication.
External API failures are handled gracefully and never crash the server.
"""
import asyncio
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.market import (
    LocationSearchResult,
    MarketAnalyzeRequest,
    MarketAnalysisOut,
    NearbyRequest,
    NearbyResultOut,
    NearbyPlaceOut,
    CompetitorSummaryOut,
    MarketOpportunityOut,
    LocationSuitabilityOut,
    MarketInsightOut,
)
from app.services.location_service import search_location, reverse_geocode
from app.services.overpass_service import (
    fetch_nearby_places,
    fetch_competitors,
    NearbyPlace,
    ALLOWED_RADII_KM,
)
from app.services.market_analyzer import analyse_market

# Two routers — mounted at different prefixes
locations_router = APIRouter(prefix="/locations", tags=["Market Intelligence"])
market_router    = APIRouter(prefix="/market",    tags=["Market Intelligence"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_biz(business_id: str, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id))
    biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Business '{business_id}' not found")
    return biz


def _place_out(p: NearbyPlace) -> NearbyPlaceOut:
    return NearbyPlaceOut(
        osm_id          = p.osm_id,
        name            = p.name,
        category        = p.category,
        latitude        = p.latitude,
        longitude       = p.longitude,
        distance_meters = p.distance_meters,
    )


# ── Location search ───────────────────────────────────────────────────────────

@locations_router.get(
    "/search",
    response_model=List[LocationSearchResult],
    summary="Search for a location by name (Nominatim / OpenStreetMap)",
)
async def location_search(
    q:            str = Query(..., min_length=2, description="Location query string"),
    limit:        int = Query(5,  ge=1, le=10),
    current_user: User = Depends(get_current_user),
) -> List[LocationSearchResult]:
    """
    Search for a location using Nominatim (free OpenStreetMap geocoding).
    Returns up to `limit` results. Returns an empty list if nothing is found
    or the external API is unavailable.
    """
    results = await search_location(q, limit=limit)
    return [
        LocationSearchResult(
            display_name = r.display_name,
            latitude     = r.latitude,
            longitude    = r.longitude,
            place_id     = r.place_id,
            country      = r.country,
            state        = r.state,
            district     = r.district,
        )
        for r in results
    ]


# ── Market analysis ───────────────────────────────────────────────────────────

@market_router.post(
    "/analyze",
    response_model=MarketAnalysisOut,
    summary="Full hyper-local market intelligence analysis",
)
async def market_analyze(
    body:         MarketAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> MarketAnalysisOut:
    """
    Run the complete market intelligence analysis for a business at a location.

    1. Fetches all nearby POIs from Overpass (OpenStreetMap)
    2. Identifies direct competitors for the selected business
    3. Scores Market Opportunity (0–100) and Location Suitability (0–100)
    4. Generates insights and recommendations

    External API failures return a valid response with zero competitors/places
    and an appropriate explanation in the insights.
    """
    biz = await _get_biz(body.business_id, db)

    # Fetch all nearby places + competitors concurrently
    nearby_task     = fetch_nearby_places(body.latitude, body.longitude, body.radius_km)
    competitor_task = fetch_competitors(body.latitude, body.longitude, biz.name, body.radius_km)

    nearby_result, comp_result = await asyncio.gather(nearby_task, competitor_task)

    # Handle external API errors gracefully
    all_places  = nearby_result.places
    competitors = comp_result.places

    # Reverse-geocode for a human-readable location name (best-effort)
    loc = await reverse_geocode(body.latitude, body.longitude)
    location_name = loc.display_name if loc else None

    analysis = analyse_market(
        latitude      = body.latitude,
        longitude     = body.longitude,
        radius_km     = body.radius_km,
        business_id   = biz.id,
        business_name = biz.name,
        all_places    = all_places,
        competitors   = competitors,
        location_name = location_name,
    )

    # Build API errors into insights if external services failed
    extra_insights = []
    for err_msg in [nearby_result.error, comp_result.error]:
        if err_msg:
            extra_insights.append(MarketInsightOut(
                icon    = "⚠️",
                message = f"Map data warning: {err_msg} — results may be incomplete.",
                level   = "warning",
            ))

    return MarketAnalysisOut(
        latitude            = analysis.latitude,
        longitude           = analysis.longitude,
        radius_km           = analysis.radius_km,
        location_name       = analysis.location_name,
        business_name       = analysis.business_name,
        business_id         = analysis.business_id,
        competitor_summary  = CompetitorSummaryOut(
            direct_count      = analysis.competitor_summary.direct_count,
            related_count     = analysis.competitor_summary.related_count,
            total_businesses  = analysis.competitor_summary.total_businesses,
            competition_level = analysis.competitor_summary.competition_level,
            density_per_sqkm  = analysis.competitor_summary.density_per_sqkm,
        ),
        opportunity = MarketOpportunityOut(
            competition_score    = analysis.opportunity.competition_score,
            infrastructure_score = analysis.opportunity.infrastructure_score,
            accessibility_score  = analysis.opportunity.accessibility_score,
            diversity_score      = analysis.opportunity.diversity_score,
            market_size_score    = analysis.opportunity.market_size_score,
            total                = analysis.opportunity.total,
        ),
        suitability = LocationSuitabilityOut(
            competition_score    = analysis.suitability.competition_score,
            infrastructure_score = analysis.suitability.infrastructure_score,
            customer_proxy_score = analysis.suitability.customer_proxy_score,
            business_density     = analysis.suitability.business_density,
            total                = analysis.suitability.total,
        ),
        nearby_places       = [_place_out(p) for p in analysis.nearby_places[:100]],
        direct_competitors  = [_place_out(p) for p in analysis.direct_competitors[:50]],
        insights            = [
            MarketInsightOut(icon=i.icon, message=i.message, level=i.level)
            for i in analysis.insights
        ] + extra_insights,
        recommendations     = analysis.recommendations,
        disclaimer          = analysis.disclaimer,
    )


# ── Nearby businesses ─────────────────────────────────────────────────────────

@market_router.post(
    "/nearby",
    response_model=NearbyResultOut,
    summary="Fetch nearby businesses from OpenStreetMap",
)
async def nearby_businesses(
    body:         NearbyRequest,
    current_user: User = Depends(get_current_user),
) -> NearbyResultOut:
    """
    Return nearby businesses, shops, and amenities for any lat/lon.
    Results are cached for 10 minutes.
    """
    result = await fetch_nearby_places(body.latitude, body.longitude, body.radius_km)

    cats: Dict[str, int] = {}
    for p in result.places:
        cats[p.category] = cats.get(p.category, 0) + 1

    return NearbyResultOut(
        latitude     = body.latitude,
        longitude    = body.longitude,
        radius_km    = body.radius_km,
        total_places = len(result.places),
        places       = [_place_out(p) for p in result.places[:100]],
        categories   = cats,
        from_cache   = result.from_cache,
        error        = result.error,
    )
