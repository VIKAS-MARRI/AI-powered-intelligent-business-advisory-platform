"""
Pydantic schemas for Phase 5 Market Intelligence API.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class MarketAnalyzeRequest(BaseModel):
    """POST /market/analyze"""
    business_id: str           = Field(..., description="Business ID from the catalogue")
    latitude:    float         = Field(..., ge=-90, le=90,   description="Location latitude")
    longitude:   float         = Field(..., ge=-180, le=180, description="Location longitude")
    radius_km:   float         = Field(5.0, ge=1, le=15,    description="Search radius in km (1–15)")

    @field_validator("radius_km")
    @classmethod
    def round_radius(cls, v: float) -> float:
        # Snap to nearest allowed value for cleaner UX
        allowed = [1, 2, 5, 10]
        return min(allowed, key=lambda x: abs(x - v))


class NearbyRequest(BaseModel):
    """POST /market/nearby"""
    latitude:  float = Field(..., ge=-90,  le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(5.0, ge=1, le=15)


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class LocationSearchResult(BaseModel):
    display_name: str
    latitude:     float
    longitude:    float
    place_id:     Optional[str] = None
    country:      Optional[str] = None
    state:        Optional[str] = None
    district:     Optional[str] = None


class NearbyPlaceOut(BaseModel):
    osm_id:          str
    name:            str
    category:        str
    latitude:        float
    longitude:       float
    distance_meters: float


class CompetitorSummaryOut(BaseModel):
    direct_count:      int
    related_count:     int
    total_businesses:  int
    competition_level: str
    density_per_sqkm:  float


class MarketOpportunityOut(BaseModel):
    competition_score:    float
    infrastructure_score: float
    accessibility_score:  float
    diversity_score:      float
    market_size_score:    float
    total:                float


class LocationSuitabilityOut(BaseModel):
    competition_score:    float
    infrastructure_score: float
    customer_proxy_score: float
    business_density:     float
    total:                float


class MarketInsightOut(BaseModel):
    icon:    str
    message: str
    level:   str


class MarketAnalysisOut(BaseModel):
    latitude:             float
    longitude:            float
    radius_km:            float
    location_name:        Optional[str]
    business_name:        str
    business_id:          str
    competitor_summary:   CompetitorSummaryOut
    opportunity:          MarketOpportunityOut
    suitability:          LocationSuitabilityOut
    nearby_places:        List[NearbyPlaceOut]
    direct_competitors:   List[NearbyPlaceOut]
    insights:             List[MarketInsightOut]
    recommendations:      List[str]
    disclaimer:           str


class NearbyResultOut(BaseModel):
    latitude:       float
    longitude:      float
    radius_km:      float
    total_places:   int
    places:         List[NearbyPlaceOut]
    categories:     Dict[str, int]
    from_cache:     bool
    error:          Optional[str]
    disclaimer:     str = (
        "Market intelligence results are based on available OpenStreetMap data "
        "and may be incomplete or outdated."
    )
