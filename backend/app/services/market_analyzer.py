"""
Market Analyzer — Phase 5 Hyper-Local Market Intelligence.

Combines data from the Overpass service with deterministic scoring formulas
to produce:

  - Market Opportunity Score  (0–100) — how attractive the market is
  - Location Suitability Score (0–100) — how suitable the physical location is
  - Competition level classification
  - Score breakdowns
  - Insights & recommendations

No AI/LLM involved — all logic is transparent and deterministic.

Scores are ESTIMATES for planning purposes only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.services.overpass_service import NearbyPlace, BUSINESS_OSM_MAPPING


# ── Data containers ────────────────────────────────────────────────────────────

@dataclass
class CompetitorSummary:
    direct_count:      int
    related_count:     int
    total_businesses:  int
    competition_level: str          # "Low" | "Moderate" | "High"
    density_per_sqkm:  float


@dataclass
class MarketOpportunityBreakdown:
    competition_score:    float   # 0–30  (higher = less competition)
    infrastructure_score: float   # 0–25  (markets, banks, transport)
    accessibility_score:  float   # 0–20  (transport nodes)
    diversity_score:      float   # 0–15  (variety of business types)
    market_size_score:    float   # 0–10  (proxy: total nearby businesses)
    total:                float   # 0–100


@dataclass
class LocationSuitabilityBreakdown:
    competition_score:    float   # 0–25
    infrastructure_score: float   # 0–30  (heavier weight vs opportunity)
    customer_proxy_score: float   # 0–25  (schools, banks, transport = foot traffic)
    business_density:     float   # 0–20  (neither too empty nor too crowded)
    total:                float   # 0–100


@dataclass
class MarketInsight:
    icon:    str
    message: str
    level:   str   # "positive" | "warning" | "neutral"


@dataclass
class MarketAnalysis:
    # Location info
    latitude:    float
    longitude:   float
    radius_km:   float
    location_name: Optional[str]

    # Business context
    business_name: str
    business_id:   str

    # Competition
    competitor_summary: CompetitorSummary

    # Scores
    opportunity: MarketOpportunityBreakdown
    suitability: LocationSuitabilityBreakdown

    # Places
    nearby_places:    List[NearbyPlace]
    direct_competitors: List[NearbyPlace]

    # Human-readable outputs
    insights:        List[MarketInsight]
    recommendations: List[str]
    disclaimer: str = (
        "Market intelligence results are based on available OpenStreetMap and "
        "public geographic data. Data may be incomplete or outdated and should "
        "be used as a planning aid rather than a guarantee of business success."
    )


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _area_sqkm(radius_km: float) -> float:
    return math.pi * radius_km ** 2


def _competition_level(direct_count: int, radius_km: float) -> str:
    """
    Classify competition:
      density = direct competitors / search area (km²)
      Low      < 0.5 / km²
      Moderate < 2.0 / km²
      High     ≥ 2.0 / km²
    """
    area = _area_sqkm(radius_km)
    density = direct_count / max(area, 0.01)
    if density < 0.5:
        return "Low"
    elif density < 2.0:
        return "Moderate"
    else:
        return "High"


def _count_by_category(places: List[NearbyPlace], categories: List[str]) -> int:
    c_set = set(categories)
    return sum(1 for p in places if p.category in c_set)


def _categorise_all(places: List[NearbyPlace]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for p in places:
        counts[p.category] = counts.get(p.category, 0) + 1
    return counts


# ── Opportunity score (0–100) ─────────────────────────────────────────────────

def _score_opportunity(
    direct_count:   int,
    all_places:     List[NearbyPlace],
    radius_km:      float,
) -> MarketOpportunityBreakdown:
    """
    Market Opportunity Score — how attractive is this market?

    Sub-scores:
      competition_score    (0–30): fewer direct competitors → higher score
      infrastructure_score (0–25): markets, banks, transport present
      accessibility_score  (0–20): transport nodes nearby
      diversity_score      (0–15): variety of business types nearby
      market_size_score    (0–10): some businesses = established demand;
                                    too many = saturated
    """
    area = _area_sqkm(radius_km)
    n    = len(all_places)
    cats = _categorise_all(all_places)

    # ── Competition sub-score (0–30) ──────────────────────────────────────────
    # 0 competitors = 30, exponential decay
    comp = 30.0 * math.exp(-direct_count * 0.4)
    comp = round(max(0.0, min(30.0, comp)), 2)

    # ── Infrastructure sub-score (0–25) ───────────────────────────────────────
    infra_cats = {"Market", "Banking & Finance", "Transport", "Education"}
    infra_count = sum(cats.get(c, 0) for c in infra_cats)
    infra = min(25.0, infra_count * 4.0)
    infra = round(infra, 2)

    # ── Accessibility sub-score (0–20) ────────────────────────────────────────
    transport_count = cats.get("Transport", 0)
    access = min(20.0, transport_count * 5.0 + (5.0 if transport_count > 0 else 0))
    access = round(access, 2)

    # ── Diversity sub-score (0–15) ────────────────────────────────────────────
    unique_cats = len(cats)
    diversity = round(min(15.0, unique_cats * 1.5), 2)

    # ── Market size sub-score (0–10) ──────────────────────────────────────────
    # Optimal density: 5–20 businesses/km² indicates an established but not
    # oversaturated market.
    density = n / max(area, 0.01)
    if density < 1:
        msize = density * 2.0      # very sparse = low score
    elif density < 20:
        msize = 10.0 * min(density / 10.0, 1.0)
    else:
        msize = max(0.0, 10.0 - (density - 20) * 0.2)
    msize = round(msize, 2)

    total = round(min(100.0, comp + infra + access + diversity + msize), 1)
    return MarketOpportunityBreakdown(
        competition_score    = comp,
        infrastructure_score = infra,
        accessibility_score  = access,
        diversity_score      = diversity,
        market_size_score    = msize,
        total                = total,
    )


# ── Suitability score (0–100) ─────────────────────────────────────────────────

def _score_suitability(
    direct_count:  int,
    all_places:    List[NearbyPlace],
    radius_km:     float,
) -> LocationSuitabilityBreakdown:
    """
    Location Suitability Score — how physically suitable is this spot?

    Differs from Opportunity by weighing customer foot-traffic proxies
    (schools, banks, markets) more heavily, and by rewarding moderate
    business density rather than low competition.

    Sub-scores:
      competition_score    (0–25): fewer competitors = better physical fit
      infrastructure_score (0–30): markets + banks + transport (heavier)
      customer_proxy_score (0–25): schools, hospitals, markets → foot traffic
      business_density     (0–20): moderate density = proven demand
    """
    area = _area_sqkm(radius_km)
    n    = len(all_places)
    cats = _categorise_all(all_places)

    # ── Competition sub-score (0–25) ──────────────────────────────────────────
    comp = 25.0 * math.exp(-direct_count * 0.35)
    comp = round(max(0.0, min(25.0, comp)), 2)

    # ── Infrastructure sub-score (0–30) ───────────────────────────────────────
    infra_cats = {"Market", "Banking & Finance", "Transport", "Education", "Medical & Health"}
    infra_count = sum(cats.get(c, 0) for c in infra_cats)
    infra = round(min(30.0, infra_count * 4.5), 2)

    # ── Customer proxy sub-score (0–25) ───────────────────────────────────────
    proxy_cats  = {"Education", "Medical & Health", "Market", "Banking & Finance", "Transport"}
    proxy_count = sum(cats.get(c, 0) for c in proxy_cats)
    proxy       = round(min(25.0, proxy_count * 3.5), 2)

    # ── Business density sub-score (0–20) ─────────────────────────────────────
    # Optimal: 3–25 /km²  — too sparse = no demand; too crowded = oversaturated
    density = n / max(area, 0.01)
    if density < 1:
        bdense = density * 4.0
    elif density <= 25:
        # Peak at density=10
        bdense = 20.0 * math.exp(-((density - 10) ** 2) / 200.0)
    else:
        bdense = max(0.0, 20.0 - (density - 25) * 0.3)
    bdense = round(max(0.0, min(20.0, bdense)), 2)

    total = round(min(100.0, comp + infra + proxy + bdense), 1)
    return LocationSuitabilityBreakdown(
        competition_score    = comp,
        infrastructure_score = infra,
        customer_proxy_score = proxy,
        business_density     = bdense,
        total                = total,
    )


# ── Insights ──────────────────────────────────────────────────────────────────

def _generate_insights(
    competitor_summary: CompetitorSummary,
    opportunity:        MarketOpportunityBreakdown,
    suitability:        LocationSuitabilityBreakdown,
    cats:               Dict[str, int],
) -> List[MarketInsight]:
    insights: List[MarketInsight] = []

    # Competition
    dc = competitor_summary.direct_count
    lvl = competitor_summary.competition_level
    if lvl == "Low":
        insights.append(MarketInsight("✅", f"Low competition — only {dc} direct competitor(s) found nearby.", "positive"))
    elif lvl == "Moderate":
        insights.append(MarketInsight("⚠️", f"Moderate competition — {dc} direct competitor(s) within the search area.", "warning"))
    else:
        insights.append(MarketInsight("🔴", f"High competition — {dc} direct competitor(s) indicate a saturated market.", "warning"))

    # Infrastructure
    if cats.get("Market", 0) > 0:
        insights.append(MarketInsight("✅", f"{cats['Market']} market(s) nearby provide built-in customer footfall.", "positive"))
    if cats.get("Banking & Finance", 0) > 0:
        insights.append(MarketInsight("✅", "Banking infrastructure nearby supports business transactions.", "positive"))
    if cats.get("Transport", 0) > 0:
        insights.append(MarketInsight("✅", "Transport nodes nearby improve accessibility for customers and suppliers.", "positive"))
    else:
        insights.append(MarketInsight("⚠️", "No transport nodes detected — consider accessibility for customers.", "warning"))

    # Education / foot traffic
    if cats.get("Education", 0) > 0:
        insights.append(MarketInsight("✅", f"{cats['Education']} school/college(s) provide consistent foot traffic.", "positive"))
    if cats.get("Medical & Health", 0) > 0:
        insights.append(MarketInsight("✅", "Medical facilities nearby indicate a community hub — good for retail.", "positive"))

    # Score-based
    if opportunity.total >= 70:
        insights.append(MarketInsight("🚀", "Strong market opportunity detected for this location.", "positive"))
    elif opportunity.total >= 45:
        insights.append(MarketInsight("⚖️", "Moderate market opportunity — plan for competitive differentiation.", "neutral"))
    else:
        insights.append(MarketInsight("⚠️", "Limited market opportunity detected. Consider a different location or business.", "warning"))

    if suitability.total >= 70:
        insights.append(MarketInsight("✅", "This is a well-suited physical location for the selected business.", "positive"))

    return insights


def _generate_recommendations(
    competitor_summary: CompetitorSummary,
    opportunity:        MarketOpportunityBreakdown,
    suitability:        LocationSuitabilityBreakdown,
) -> List[str]:
    recs: List[str] = []
    lvl = competitor_summary.competition_level

    if lvl == "Low":
        recs.append("This is a strong opportunity — low competition means you can build a loyal customer base quickly.")
    elif lvl == "Moderate":
        recs.append("Differentiate your offering (quality, pricing, or service) to stand out from existing competitors.")
    else:
        recs.append("Consider expanding the search radius or evaluating alternative locations with lower competition.")

    if opportunity.infrastructure_score < 10:
        recs.append("Limited nearby infrastructure — consider proximity to markets or transport hubs before committing.")
    if suitability.customer_proxy_score < 8:
        recs.append("Low customer foot-traffic proxies detected — marketing investment will be higher to attract customers.")
    if opportunity.total >= 60 and suitability.total >= 60:
        recs.append("Both opportunity and suitability scores are strong — this location is recommended for further on-ground assessment.")
    elif opportunity.total < 40:
        recs.append("Consider searching for a location with more infrastructure and lower competition density.")

    recs.append(
        "Conduct an on-site visit to verify OSM data accuracy — map data may be outdated in rural areas."
    )
    return recs


# ── Public API ────────────────────────────────────────────────────────────────

def analyse_market(
    latitude:        float,
    longitude:       float,
    radius_km:       float,
    business_id:     str,
    business_name:   str,
    all_places:      List[NearbyPlace],
    competitors:     List[NearbyPlace],
    location_name:   Optional[str] = None,
) -> MarketAnalysis:
    """
    Run the full market analysis given pre-fetched place data.

    Parameters:
      all_places   — all nearby POIs (from fetch_nearby_places)
      competitors  — direct competitors (from fetch_competitors)
    """
    direct_count  = len(competitors)
    related_count = max(0, len(all_places) - direct_count)
    area          = _area_sqkm(radius_km)
    density       = direct_count / max(area, 0.01)
    comp_level    = _competition_level(direct_count, radius_km)
    cats          = _categorise_all(all_places)

    competitor_summary = CompetitorSummary(
        direct_count      = direct_count,
        related_count     = related_count,
        total_businesses  = len(all_places),
        competition_level = comp_level,
        density_per_sqkm  = round(density, 3),
    )

    opportunity = _score_opportunity(direct_count, all_places, radius_km)
    suitability = _score_suitability(direct_count, all_places, radius_km)
    insights    = _generate_insights(competitor_summary, opportunity, suitability, cats)
    recs        = _generate_recommendations(competitor_summary, opportunity, suitability)

    return MarketAnalysis(
        latitude            = latitude,
        longitude           = longitude,
        radius_km           = radius_km,
        location_name       = location_name,
        business_name       = business_name,
        business_id         = business_id,
        competitor_summary  = competitor_summary,
        opportunity         = opportunity,
        suitability         = suitability,
        nearby_places       = all_places,
        direct_competitors  = competitors,
        insights            = insights,
        recommendations     = recs,
    )
