"""
Demo Mode API — Phase 11, Section 9.

GET  /demo/status          — check if demo mode is active
GET  /demo/profiles        — return sample entrepreneur profiles
GET  /demo/scenarios       — return guided demo scenarios

All data is clearly labeled as "Demo Data".
Demo data is never mixed with real user data.
"""
from typing import Any, Dict, List

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/demo", tags=["Demo Mode"])

# ── Demo Profiles ─────────────────────────────────────────────────────────────

_DEMO_PROFILES: List[Dict[str, Any]] = [
    {
        "id":              "demo-profile-1",
        "label":          "💡 Demo Data",
        "name":           "Priya Devi",
        "description":    "Rural Tailoring Entrepreneur",
        "available_capital": 50000,
        "skills":         "tailoring, stitching, embroidery",
        "business_interests": "tailoring shop, garments",
        "state":          "Telangana",
        "monthly_income_goal": 15000,
        "experience_years":  2,
        "scenario":       "Looking to start a tailoring business with limited capital and service skills",
        "is_demo":        True,
    },
    {
        "id":              "demo-profile-2",
        "label":          "💡 Demo Data",
        "name":           "Raju Kumar",
        "description":    "Small Food Entrepreneur",
        "available_capital": 150000,
        "skills":         "cooking, food preparation",
        "business_interests": "food stall, tiffin service, kirana store",
        "state":          "Andhra Pradesh",
        "monthly_income_goal": 25000,
        "experience_years":  3,
        "scenario":       "Food business interest with moderate capital and wants local market analysis",
        "is_demo":        True,
    },
    {
        "id":              "demo-profile-3",
        "label":          "💡 Demo Data",
        "name":           "Lakshmi Bai",
        "description":    "Agriculture Entrepreneur",
        "available_capital": 200000,
        "skills":         "farming, dairy, animal husbandry",
        "business_interests": "dairy farming, organic farming, agro-processing",
        "state":          "Karnataka",
        "monthly_income_goal": 30000,
        "experience_years":  5,
        "scenario":       "Agriculture interest, rural location, looking for government schemes and investment advice",
        "is_demo":        True,
    },
]

_DEMO_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id":          "find-business",
        "icon":        "💡",
        "title":       "Find My Business",
        "description": "Get AI-powered personalized business recommendations based on your capital and skills.",
        "route":       "/recommendations",
        "feature":     "Phase 2 — Recommendation Engine",
        "question":    "What business can I start with ₹1 lakh with tailoring skills?",
        "is_demo":     True,
    },
    {
        "id":          "plan-investment",
        "icon":        "💰",
        "title":       "Plan My Investment",
        "description": "See financial analysis and OR-Tools investment optimization.",
        "route":       "/investment-optimizer",
        "feature":     "Phase 3 + Phase 4 — Financial Intelligence & OR-Tools",
        "question":    "How should I invest ₹2 lakh for best returns in a food business?",
        "is_demo":     True,
    },
    {
        "id":          "analyze-market",
        "icon":        "🗺️",
        "title":       "Analyze My Market",
        "description": "Get hyper-local market intelligence using OpenStreetMap data.",
        "route":       "/market-intelligence",
        "feature":     "Phase 5 — OpenStreetMap + Overpass API",
        "question":    "What is the competition like for a dairy business in Telangana?",
        "is_demo":     True,
    },
    {
        "id":          "government-support",
        "icon":        "🏛️",
        "title":       "Find Government Support",
        "description": "Discover PMEGP, MUDRA, and other government schemes you may qualify for.",
        "route":       "/scheme-support",
        "feature":     "Phase 6 — Government Scheme Intelligence",
        "question":    "What government schemes are available for dairy farming?",
        "is_demo":     True,
    },
    {
        "id":          "ai-advisor",
        "icon":        "🤖",
        "title":       "Ask AI Advisor",
        "description": "Experience the multi-agent AI advisory system with a real question.",
        "route":       "/advisor",
        "feature":     "Phase 7 — LangGraph Multi-Agent System",
        "question":    "What is the best business for a rural woman with ₹50,000 and tailoring skills in Telangana?",
        "is_demo":     True,
    },
    {
        "id":          "analytics",
        "icon":        "📊",
        "title":       "Track Progress",
        "description": "See the entrepreneur analytics and goal tracking dashboard.",
        "route":       "/analytics",
        "feature":     "Phase 9 — Entrepreneur Analytics",
        "question":    None,
        "is_demo":     True,
    },
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", summary="Check if demo mode is active")
async def demo_status() -> Dict[str, Any]:
    return {
        "demo_mode": settings.DEMO_MODE,
        "message": (
            "Demo mode is ACTIVE. Sample data is available."
            if settings.DEMO_MODE
            else "Demo mode is disabled. Running in live mode."
        ),
        "label": "Demo Data" if settings.DEMO_MODE else None,
    }


@router.get("/profiles", summary="Get sample entrepreneur profiles for demos")
async def demo_profiles() -> Dict[str, Any]:
    return {
        "profiles":  _DEMO_PROFILES,
        "count":     len(_DEMO_PROFILES),
        "is_demo":   True,
        "disclaimer":"These are sample demo profiles for demonstration purposes only.",
    }


@router.get("/scenarios", summary="Get guided demo scenarios")
async def demo_scenarios() -> Dict[str, Any]:
    return {
        "scenarios": _DEMO_SCENARIOS,
        "count":     len(_DEMO_SCENARIOS),
        "is_demo":   True,
        "disclaimer":"These are guided demonstration scenarios for hackathon judges.",
    }
