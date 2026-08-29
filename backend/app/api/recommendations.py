"""
Recommendation engine endpoint.
POST /recommendations — generate personalised business recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.business import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    ScoreBreakdown,
)
from app.schemas.business import BusinessPublic
from app.services.recommendation_engine import (
    score_business,
    generate_reasons,
    profile_completeness,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post(
    "",
    response_model=RecommendationResponse,
    summary="Generate personalised business recommendations",
)
async def get_recommendations(
    body: RecommendationRequest = RecommendationRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Score all businesses against the authenticated user's profile
    and return the top N recommendations.

    Optional request body can temporarily override profile values.
    """
    # Resolve effective parameters (request body overrides user profile)
    capital        = body.available_capital    if body.available_capital    is not None else current_user.available_capital
    skills         = body.skills               if body.skills               is not None else current_user.skills
    interests      = body.business_interests   if body.business_interests   is not None else current_user.business_interests
    income_goal    = body.monthly_income_goal  if body.monthly_income_goal  is not None else current_user.monthly_income_goal
    preferred_risk = body.preferred_risk
    top_n          = body.top_n

    # Load all businesses
    result = await db.execute(select(Business))
    all_businesses: list[Business] = list(result.scalars().all())

    if not all_businesses:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Business database is empty. Please run: python -m app.seed_businesses",
        )

    # Score every business
    scored: list[dict] = []
    for biz in all_businesses:
        scores = score_business(
            biz=biz,
            capital=capital,
            skills=skills,
            interests=interests,
            income_goal=income_goal,
            preferred_risk=preferred_risk,
        )
        scored.append({"biz": biz, "scores": scores})

    # Sort by final score descending
    scored.sort(key=lambda x: x["scores"]["final"], reverse=True)

    # Build recommendation items
    items: list[RecommendationItem] = []
    for rank, entry in enumerate(scored[:top_n], start=1):
        biz: Business = entry["biz"]
        scores: dict = entry["scores"]
        reasons = generate_reasons(scores, biz, capital)

        items.append(
            RecommendationItem(
                rank=rank,
                business=BusinessPublic.from_orm_with_extras(biz),
                final_score=scores["final"],
                score_breakdown=ScoreBreakdown(
                    budget=scores["budget"],
                    skills=scores["skills"],
                    interest=scores["interest"],
                    profit=scores["profit"],
                    risk=scores["risk"],
                    income_goal=scores["income_goal"],
                ),
                reasons=reasons,
            )
        )

    completeness = profile_completeness(current_user)

    return RecommendationResponse(
        recommendations=items,
        profile_completeness=completeness,
        total_businesses_scored=len(all_businesses),
    )
