"""
Phase 8 API routes — Personalized Recommendations, Natural Query,
Saved Businesses, Interaction Tracking, Entrepreneur Profile.

All routes are JWT-protected. Backward-compatible with Phase 2 /recommendations.

New endpoints:
  POST /recommendations/personalized
  POST /recommendations/natural-query
  POST /recommendations/{business_id}/interaction
  GET  /recommendations/preferences
  GET  /recommendations/profile
  PUT  /recommendations/profile
  POST /saved-businesses/{business_id}
  GET  /saved-businesses
  DELETE /saved-businesses/{business_id}
"""
from __future__ import annotations

import logging
from collections import Counter
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.business import Business
from app.models.phase8 import (
    EntrepreneurProfile,
    RecommendationInteraction,
    SavedBusiness,
)
from app.models.user import User
from app.schemas.phase8 import (
    EntrepreneurProfileIn,
    EntrepreneurProfileOut,
    ExtractedIntent,
    InteractionOut,
    InteractionRequest,
    NaturalQueryRequest,
    NaturalQueryResponse,
    PersonalizedBreakdown,
    PersonalizedRecommendationItem,
    PersonalizedRecommendationRequest,
    PersonalizedRecommendationResponse,
    PersonalizedScoreRaw,
    PreferenceSummary,
    RecommendationExplanation,
    SavedBusinessIn,
    SavedBusinessListOut,
    SavedBusinessOut,
    SemanticMatchDetail,
    SemanticMatchSummary,
    FinancialOutlook,
    NaturalQueryResponse,
)
from app.services.personalized_recommendation_engine import (
    explain_recommendation,
    personalized_score,
)
from app.services.recommendation_engine import profile_completeness
from app.services.semantic_matcher import extract_query_intent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Phase 8 — Personalized"])
saved_router = APIRouter(prefix="/saved-businesses", tags=["Phase 8 — Saved Businesses"])

VALID_INTERACTION_TYPES = {"viewed", "saved", "compared", "dismissed", "explored"}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_businesses(db: AsyncSession) -> List[Business]:
    result = await db.execute(select(Business))
    businesses = list(result.scalars().all())
    if not businesses:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Business database is empty. Run: python -m app.seed_businesses",
        )
    return businesses


async def _saved_ids(db: AsyncSession, user_id: str) -> set:
    result = await db.execute(
        select(SavedBusiness.business_id).where(SavedBusiness.user_id == user_id)
    )
    return set(r[0] for r in result.all())


async def _get_preference_data(db: AsyncSession, user_id: str) -> Optional[Dict]:
    """Build preference data from interaction history."""
    result = await db.execute(
        select(RecommendationInteraction).where(
            RecommendationInteraction.user_id == user_id
        )
    )
    interactions = list(result.scalars().all())
    if not interactions:
        return None

    # Fetch business categories for each interaction
    all_biz_ids = list({i.business_id for i in interactions})
    biz_result  = await db.execute(
        select(Business.id, Business.category, Business.risk_level).where(
            Business.id.in_(all_biz_ids)
        )
    )
    biz_map = {row[0]: {"category": row[1], "risk": row[2]} for row in biz_result.all()}

    preferred_categories: Counter = Counter()
    avoided_categories:   Counter = Counter()
    risk_preferences:     Counter = Counter()

    for interaction in interactions:
        biz_info = biz_map.get(interaction.business_id)
        if not biz_info:
            continue
        cat  = biz_info["category"]
        risk = biz_info["risk"]
        if interaction.interaction_type in ("explored", "saved", "compared"):
            preferred_categories[cat] += 1
            risk_preferences[risk]    += 1
        elif interaction.interaction_type == "dismissed":
            avoided_categories[cat] += 1

    preferred_risk = risk_preferences.most_common(1)[0][0] if risk_preferences else None

    return {
        "preferred_categories": dict(preferred_categories),
        "avoided_categories":   dict(avoided_categories),
        "preferred_risk":       preferred_risk,
    }


def _build_item(
    rank: int,
    biz: Business,
    scores: Dict,
    saved_ids: set,
) -> PersonalizedRecommendationItem:
    """Construct a PersonalizedRecommendationItem from scores dict."""
    explanation_data = explain_recommendation(scores, biz, scores.get("_capital"))
    raw = scores.get("raw_scores", {})
    bd  = scores.get("breakdown", {})
    sem = scores.get("semantic_detail", {})

    return PersonalizedRecommendationItem(
        rank=rank,
        business_id=biz.id,
        business_name=biz.name,
        category=biz.category,
        business_type=biz.business_type,
        risk_level=biz.risk_level,
        min_investment=biz.min_investment,
        max_investment=biz.max_investment,
        monthly_profit_min=biz.estimated_monthly_profit_min,
        monthly_profit_max=biz.estimated_monthly_profit_max,
        setup_time_weeks_min=biz.setup_time_weeks_min,
        setup_time_weeks_max=biz.setup_time_weeks_max,
        suitable_for_rural=biz.suitable_for_rural,
        description=biz.description,
        required_skills=biz.required_skills,
        final_score=scores["final_score"],
        breakdown=PersonalizedBreakdown(
            semantic_skill=bd.get("semantic_skill", 0),
            budget=bd.get("budget", 0),
            market_opportunity=bd.get("market_opportunity", 0),
            financial_potential=bd.get("financial_potential", 0),
            experience=bd.get("experience", 0),
            gov_support=bd.get("gov_support", 0),
            risk=bd.get("risk", 0),
            interest=bd.get("interest", 0),
            income_goal=bd.get("income_goal", 0),
            location=bd.get("location", 0),
            preference_modifier=bd.get("preference_modifier", 0),
        ),
        raw_scores=PersonalizedScoreRaw(
            semantic_skill=raw.get("semantic_skill", 0),
            budget=raw.get("budget", 0),
            market_opportunity=raw.get("market_opportunity", 0),
            financial_potential=raw.get("financial_potential", 0),
            experience=raw.get("experience", 0),
            gov_support=raw.get("gov_support", 0),
            risk=raw.get("risk", 0),
            interest=raw.get("interest", 0),
            income_goal=raw.get("income_goal", 0),
            location=raw.get("location", 0),
        ),
        semantic_detail=SemanticMatchDetail(
            semantic_score=sem.get("semantic_score", 0),
            matched_concepts=sem.get("matched_concepts", []),
            explanation=sem.get("explanation", ""),
            method=sem.get("method", "default"),
        ),
        explanation=RecommendationExplanation(
            why_recommended=explanation_data["why_recommended"],
            strengths=explanation_data["strengths"],
            challenges=explanation_data["challenges"],
            next_steps=explanation_data["next_steps"],
            financial_outlook=FinancialOutlook(
                min_investment=biz.min_investment,
                max_investment=biz.max_investment,
                monthly_profit_min=biz.estimated_monthly_profit_min,
                monthly_profit_max=biz.estimated_monthly_profit_max,
                risk_level=biz.risk_level,
            ),
            semantic_match=SemanticMatchSummary(
                score=sem.get("semantic_score", 0),
                concepts=sem.get("matched_concepts", []),
                explanation=sem.get("explanation", ""),
            ),
            disclaimer=explanation_data["disclaimer"],
        ),
        is_saved=biz.id in saved_ids,
    )


# ── POST /recommendations/personalized ───────────────────────────────────────

@router.post(
    "/personalized",
    response_model=PersonalizedRecommendationResponse,
    summary="Phase 8 personalized recommendations with semantic skill matching",
)
async def personalized_recommendations(
    body:         PersonalizedRecommendationRequest = PersonalizedRecommendationRequest(),
    current_user: User                              = Depends(get_current_user),
    db:           AsyncSession                      = Depends(get_db),
) -> PersonalizedRecommendationResponse:
    """
    Score all businesses using 10-factor personalized engine.
    Returns transparent score breakdowns and explainable AI reasons.
    """
    capital      = body.available_capital  or current_user.available_capital
    skills       = body.skills             or current_user.skills
    interests    = body.business_interests or current_user.business_interests
    income_goal  = body.monthly_income_goal or current_user.monthly_income_goal
    pref_risk    = body.preferred_risk
    exp_years    = body.experience_years   or current_user.experience_years
    loc_type     = body.location_type

    # Load profile extension
    prof_result  = await db.execute(
        select(EntrepreneurProfile).where(EntrepreneurProfile.user_id == current_user.id)
    )
    eprofile = prof_result.scalars().first()
    if eprofile:
        loc_type  = loc_type  or eprofile.location_type
        exp_years = exp_years or None  # keep body value

    # Preference data
    pref_data = None
    if body.use_preferences:
        pref_data = await _get_preference_data(db, current_user.id)

    all_businesses = await _load_businesses(db)
    saved_ids      = await _saved_ids(db, current_user.id)

    scored = []
    for biz in all_businesses:
        scores = personalized_score(
            biz=biz, capital=capital, skills=skills, interests=interests,
            income_goal=income_goal, preferred_risk=pref_risk,
            experience_years=exp_years, location_type=loc_type,
            preference_data=pref_data,
        )
        scores["_capital"] = capital   # pass-through for explanation builder
        scored.append((biz, scores))

    scored.sort(key=lambda x: x[1]["final_score"], reverse=True)

    items = [
        _build_item(rank, biz, scores, saved_ids)
        for rank, (biz, scores) in enumerate(scored[: body.top_n], start=1)
    ]

    return PersonalizedRecommendationResponse(
        recommendations=items,
        profile_completeness=profile_completeness(current_user),
        total_businesses_scored=len(all_businesses),
        ai_mode="data",
    )


# ── POST /recommendations/natural-query ──────────────────────────────────────

@router.post(
    "/natural-query",
    response_model=NaturalQueryResponse,
    summary="Search businesses using natural language",
)
async def natural_language_query(
    body:         NaturalQueryRequest,
    current_user: User          = Depends(get_current_user),
    db:           AsyncSession  = Depends(get_db),
) -> NaturalQueryResponse:
    """
    Parse a natural language query, extract intent, run personalized scoring.
    Always has a deterministic fallback.
    """
    parse_method = "deterministic"
    intent       = extract_query_intent(body.query)

    # Optionally enrich intent with AI
    if body.use_ai_parsing:
        try:
            from app.services.ai_service import ai_service
            if ai_service.is_available():
                from app.agents.prompts import GROUNDING_INSTRUCTION
                prompt = (
                    f"Parse this business query and extract structured information.\n"
                    f"Query: {body.query}\n"
                    f"Return JSON with keys: budget (number or null), skills (string), "
                    f"risk_preference (Low/Medium/High or null), "
                    f"business_type_hints (array of strings), location_type (rural/semi_urban/urban or null).\n"
                    f"JSON only, no explanation."
                )
                ai_result = await ai_service.generate_json(prompt)
                if ai_result and isinstance(ai_result, dict):
                    # Merge AI result into intent, preserving deterministic fallback values
                    if ai_result.get("budget") and not intent["budget"]:
                        intent["budget"] = float(ai_result["budget"])
                    if ai_result.get("skills") and not intent["skills"]:
                        intent["skills"] = str(ai_result["skills"])
                    if ai_result.get("risk_preference") and not intent["risk_preference"]:
                        intent["risk_preference"] = str(ai_result["risk_preference"])
                    parse_method = "ai-enhanced"
        except Exception:
            pass   # Graceful fallback — deterministic intent is already set

    # Fall back to user profile where intent has no value
    capital   = intent["budget"]   or current_user.available_capital
    skills    = intent["skills"]   or current_user.skills or ""
    risk      = intent["risk_preference"] or None

    all_businesses = await _load_businesses(db)
    saved_ids      = await _saved_ids(db, current_user.id)

    scored = []
    for biz in all_businesses:
        # Filter by business type hints
        if intent["business_type_hints"]:
            cat_match = any(
                hint.lower() in biz.business_type.lower() or hint.lower() in biz.category.lower()
                for hint in intent["business_type_hints"]
            )
            # still score all; just boost type matches
        else:
            cat_match = True

        scores = personalized_score(
            biz=biz, capital=capital, skills=skills,
            interests=body.query,   # use full query as interest signal
            income_goal=current_user.monthly_income_goal,
            preferred_risk=risk,
            location_type=intent["location_type"],
        )
        # Small boost for matching business type hints
        if cat_match and intent["business_type_hints"]:
            scores["final_score"] = min(100, scores["final_score"] + 3)
        scores["_capital"] = capital
        scored.append((biz, scores))

    scored.sort(key=lambda x: x[1]["final_score"], reverse=True)

    items = [
        _build_item(rank, biz, scores, saved_ids)
        for rank, (biz, scores) in enumerate(scored[: body.top_n], start=1)
    ]

    return NaturalQueryResponse(
        recommendations=items,
        extracted_intent=ExtractedIntent(
            budget=intent["budget"],
            skills=intent["skills"],
            risk_preference=intent["risk_preference"],
            business_type_hints=intent["business_type_hints"],
            location_type=intent["location_type"],
            raw_query=body.query,
        ),
        parse_method=parse_method,
    )


# ── POST /recommendations/{business_id}/interaction ───────────────────────────

@router.post(
    "/{business_id}/interaction",
    response_model=InteractionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Track user interaction with a recommended business",
)
async def record_interaction(
    business_id:  str              = Path(...),
    body:         InteractionRequest = ...,
    current_user: User             = Depends(get_current_user),
    db:           AsyncSession     = Depends(get_db),
) -> InteractionOut:
    if body.interaction_type not in VALID_INTERACTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"interaction_type must be one of: {', '.join(sorted(VALID_INTERACTION_TYPES))}",
        )
    # Verify business exists
    biz_result = await db.execute(select(Business.id).where(Business.id == business_id))
    if not biz_result.scalar():
        raise HTTPException(status_code=404, detail="Business not found")

    interaction = RecommendationInteraction(
        user_id=current_user.id,
        business_id=business_id,
        interaction_type=body.interaction_type,
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return InteractionOut.model_validate(interaction)


# ── GET /recommendations/preferences ─────────────────────────────────────────

@router.get(
    "/preferences",
    response_model=PreferenceSummary,
    summary="Get user preference summary derived from interaction history",
)
async def get_preferences(
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> PreferenceSummary:
    pref = await _get_preference_data(db, current_user.id)
    total_result = await db.execute(
        select(func.count()).select_from(RecommendationInteraction).where(
            RecommendationInteraction.user_id == current_user.id
        )
    )
    total = total_result.scalar() or 0

    return PreferenceSummary(
        preferred_categories=pref["preferred_categories"] if pref else {},
        avoided_categories=pref["avoided_categories"]     if pref else {},
        preferred_risk=pref["preferred_risk"]             if pref else None,
        total_interactions=total,
    )


# ── GET /recommendations/profile ─────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=EntrepreneurProfileOut,
    summary="Get entrepreneur intelligence profile",
)
async def get_entrepreneur_profile(
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> EntrepreneurProfileOut:
    result = await db.execute(
        select(EntrepreneurProfile).where(EntrepreneurProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create one first via PUT.")
    return EntrepreneurProfileOut.model_validate(profile)


# ── PUT /recommendations/profile ─────────────────────────────────────────────

@router.put(
    "/profile",
    response_model=EntrepreneurProfileOut,
    summary="Create or update entrepreneur intelligence profile",
)
async def upsert_entrepreneur_profile(
    body:         EntrepreneurProfileIn,
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> EntrepreneurProfileOut:
    result = await db.execute(
        select(EntrepreneurProfile).where(EntrepreneurProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()

    if profile:
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(profile, field, value)
    else:
        profile = EntrepreneurProfile(user_id=current_user.id, **body.model_dump(exclude_none=True))
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return EntrepreneurProfileOut.model_validate(profile)


# ══════════════════════════════════════════════════════════════════════════════
# Saved Businesses router
# ══════════════════════════════════════════════════════════════════════════════

@saved_router.post(
    "/{business_id}",
    response_model=SavedBusinessOut,
    status_code=status.HTTP_201_CREATED,
    summary="Save a business to favourites",
)
async def save_business(
    business_id:  str             = Path(...),
    body:         SavedBusinessIn = SavedBusinessIn(),
    current_user: User            = Depends(get_current_user),
    db:           AsyncSession    = Depends(get_db),
) -> SavedBusinessOut:
    # Verify business exists
    biz_result = await db.execute(select(Business.id).where(Business.id == business_id))
    if not biz_result.scalar():
        raise HTTPException(status_code=404, detail="Business not found")

    # Check for duplicate
    dup = await db.execute(
        select(SavedBusiness).where(
            and_(SavedBusiness.user_id == current_user.id, SavedBusiness.business_id == business_id)
        )
    )
    if dup.scalars().first():
        raise HTTPException(status_code=409, detail="Business already saved")

    saved = SavedBusiness(
        user_id=current_user.id,
        business_id=business_id,
        notes=body.notes,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    return SavedBusinessOut.model_validate(saved)


@saved_router.get(
    "",
    response_model=SavedBusinessListOut,
    summary="List saved / favourite businesses",
)
async def list_saved_businesses(
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> SavedBusinessListOut:
    result = await db.execute(
        select(SavedBusiness).where(SavedBusiness.user_id == current_user.id)
        .order_by(SavedBusiness.created_at.desc())
    )
    items = list(result.scalars().all())
    return SavedBusinessListOut(
        items=[SavedBusinessOut.model_validate(i) for i in items],
        total=len(items),
    )


@saved_router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a business from favourites",
    response_model=None,
)
async def delete_saved_business(
    business_id:  str         = Path(...),
    current_user: User        = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(SavedBusiness).where(
            and_(SavedBusiness.user_id == current_user.id, SavedBusiness.business_id == business_id)
        )
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Saved business not found")
