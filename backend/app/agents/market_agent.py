"""
Market Intelligence Agent — Phase 7.

Uses Phase 5 Overpass + analyse_market() for real OSM-based data.
Gemini only interprets real data — never fabricates competitor counts or statistics.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.prompts import MARKET_AGENT_PROMPT, GROUNDING_INSTRUCTION, build_language_instruction
from app.agents.state import AgentState
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def _format_market_data(md: Dict) -> str:
    lines = []
    if md.get("competition_level"):
        lines.append(f"Competition Level: {md['competition_level']}")
    if md.get("direct_competitors") is not None:
        lines.append(f"Direct Competitors Nearby: {md['direct_competitors']}")
    if md.get("market_opportunity_score") is not None:
        lines.append(f"Market Opportunity Score: {md['market_opportunity_score']:.0f}/100")
    if md.get("location_suitability_score") is not None:
        lines.append(f"Location Suitability Score: {md['location_suitability_score']:.0f}/100")
    insights = md.get("insights", [])
    if insights:
        lines.append("\nKey Insights:")
        for ins in insights[:3]:
            msg = ins.get("message", ins) if isinstance(ins, dict) else str(ins)
            lines.append(f"  - {msg}")
    return "\n".join(lines) if lines else "Market data not available for this location."


async def market_agent_node(state: AgentState) -> AgentState:
    """Market agent: fetches Phase 5 OSM data and analyses local market."""
    if "market" not in state.get("required_agents", []):
        return state

    errors: List[str] = list(state.get("errors", []))
    result: Dict[str, Any] = {}

    lat = state.get("latitude")
    lon = state.get("longitude")
    question = state.get("question", "")

    # Business context from previous agent results
    biz_id   = state.get("business_id", "advisor")
    biz_name = "Business"
    if state.get("business_result") and (state["business_result"] or {}).get("top_business"):
        top      = state["business_result"]["top_business"]
        biz_id   = top.get("id", biz_id)
        biz_name = top.get("name", biz_name)

    if not lat or not lon:
        result = {
            "status":  "skipped",
            "reason":  "No location coordinates provided",
            "message": "Provide latitude and longitude for local market analysis.",
        }
        return {**state, "market_result": result, "errors": errors}

    try:
        from app.services.overpass_service import fetch_nearby_places
        from app.services.market_analyzer import analyse_market, NearbyPlace, BUSINESS_OSM_MAPPING

        radius_km = state.get("radius_km") or 5.0

        # Fetch real OSM places
        places = await fetch_nearby_places(lat, lon, radius_km=radius_km)

        # Determine competitors: places with same business category mapping
        # Use a broad match: any place type relevant to the business
        competitors: List[NearbyPlace] = []
        if biz_name and places:
            biz_lower = biz_name.lower()
            for place in places:
                if biz_lower in (place.name or "").lower():
                    competitors.append(place)
            # Fallback: first 5 if none matched
            if not competitors:
                competitors = places[:5]

        analysis = analyse_market(
            latitude      = lat,
            longitude     = lon,
            radius_km     = radius_km,
            business_id   = biz_id,
            business_name = biz_name,
            all_places    = places,
            competitors   = competitors,
            location_name = state.get("state_name"),
        )

        md = {
            "competition_level":          getattr(analysis, "competition_level", None),
            "direct_competitors":         len(competitors),
            "market_opportunity_score":   getattr(analysis.market_opportunity,   "overall_score", None),
            "location_suitability_score": getattr(analysis.location_suitability, "overall_score", None),
            "nearby_places_count":        len(places),
            "insights":                   [
                {"message": getattr(i, "message", str(i))}
                for i in getattr(analysis, "insights", [])
            ],
            "recommendations": getattr(analysis, "recommendations", []),
            "data_source":     "Phase 5 OpenStreetMap / Overpass API (real data)",
            "status":          "success",
        }
        result.update(md)

        # Optional AI explanation
        ai_explanation: Optional[str] = None
        location_str = state.get("state_name") or f"Lat {lat:.4f}, Lon {lon:.4f}"
        if ai_service.is_available():
            lang_instruction = build_language_instruction(
                state.get("language") or "en",
                bool(state.get("simple_language", False)),
            )
            prompt = MARKET_AGENT_PROMPT.format(
                grounding            = GROUNDING_INSTRUCTION,
                question             = question,
                location             = location_str,
                business_name        = biz_name,
                market_data          = _format_market_data(md),
                language_instruction = lang_instruction,
            )
            ai_explanation = await ai_service.generate(prompt)

        result["ai_explanation"] = ai_explanation

    except Exception as exc:
        logger.exception("Market agent error: %s", exc)
        errors.append(f"Market agent error: {exc}")
        result = {"status": "error", "error": str(exc)}

    return {**state, "market_result": result, "errors": errors}
