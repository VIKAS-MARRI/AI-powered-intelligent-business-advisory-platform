"""
Government Scheme API endpoints — Phase 6.

GET  /schemes                   — list all active schemes (filterable)
GET  /schemes/categories        — get available categories and sectors
GET  /schemes/{id}              — get full scheme details
POST /schemes/match             — match schemes to a business/user profile (JWT)
POST /schemes/compare           — compare 2–4 specific schemes (JWT)
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.business import Business
from app.models.scheme import Scheme
from app.models.user import User
from app.schemas.scheme import (
    CategoriesOut,
    FundingGapOut,
    MatchResultOut,
    SchemeCompareRequest,
    SchemeMatchOut,
    SchemeMatchRequest,
    SchemeOut,
    SchemeSummaryOut,
    SchemesListOut,
    ScoreBreakdownOut,
    EligibilityFlagOut,
)
from app.services.scheme_matcher import (
    MatchRequest,
    MatchResult,
    DISCLAIMER,
    compare_schemes,
    match_schemes,
)

router = APIRouter(prefix="/schemes", tags=["Government Schemes"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_field(raw: str) -> List[str]:
    """Parse a JSON-array string stored in a Text column."""
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else [str(val)]
    except Exception:
        return [raw] if raw else []


def _to_summary(s: Scheme) -> SchemeSummaryOut:
    return SchemeSummaryOut(
        id                     = s.id,
        name                   = s.name,
        slug                   = s.slug,
        short_description      = s.short_description,
        category               = s.category,
        sector                 = s.sector,
        location_scope         = s.location_scope,
        key_benefit            = s.key_benefit,
        maximum_loan_amount    = s.maximum_loan_amount,
        maximum_subsidy_amount = s.maximum_subsidy_amount,
        subsidy_percentage     = s.subsidy_percentage,
        is_women_specific      = s.is_women_specific,
        is_sc_st_specific      = s.is_sc_st_specific,
        is_rural_specific      = s.is_rural_specific,
        is_youth_specific      = s.is_youth_specific,
        official_url           = s.official_url,
        data_status            = s.data_status,
        last_reviewed          = s.last_reviewed,
    )


def _to_full(s: Scheme) -> SchemeOut:
    return SchemeOut(
        id                       = s.id,
        name                     = s.name,
        slug                     = s.slug,
        short_description        = s.short_description,
        full_description         = s.full_description,
        category                 = s.category,
        sector                   = s.sector,
        target_beneficiaries     = s.target_beneficiaries,
        location_scope           = s.location_scope,
        states                   = s.states,
        business_categories      = s.business_categories,
        minimum_age              = s.minimum_age,
        maximum_age              = s.maximum_age,
        minimum_investment       = s.minimum_investment,
        maximum_investment       = s.maximum_investment,
        maximum_loan_amount      = s.maximum_loan_amount,
        maximum_subsidy_amount   = s.maximum_subsidy_amount,
        subsidy_percentage       = s.subsidy_percentage,
        key_benefit              = s.key_benefit,
        eligibility_requirements = _parse_json_field(s.eligibility_requirements),
        required_documents       = _parse_json_field(s.required_documents),
        application_steps        = _parse_json_field(s.application_steps),
        is_women_specific        = s.is_women_specific,
        is_sc_st_specific        = s.is_sc_st_specific,
        is_rural_specific        = s.is_rural_specific,
        is_youth_specific        = s.is_youth_specific,
        official_source          = s.official_source,
        official_url             = s.official_url,
        data_status              = s.data_status,
        last_reviewed            = s.last_reviewed,
        sort_order               = s.sort_order,
    )


def _match_to_out(m) -> SchemeMatchOut:
    return SchemeMatchOut(
        scheme_id         = m.scheme_id,
        scheme_name       = m.scheme_name,
        scheme_slug       = m.scheme_slug,
        category          = m.category,
        sector            = m.sector,
        data_status       = m.data_status,
        key_benefit       = m.key_benefit,
        official_url      = m.official_url,
        score_breakdown   = ScoreBreakdownOut(**m.score_breakdown.__dict__),
        eligibility       = EligibilityFlagOut(**m.eligibility.__dict__),
        match_reasons     = m.match_reasons,
        funding_relevance = m.funding_relevance,
        tags              = m.tags,
    )


async def _load_all_schemes(db: AsyncSession) -> List[Scheme]:
    result = await db.execute(select(Scheme).where(Scheme.is_active == True).order_by(Scheme.sort_order))
    return list(result.scalars().all())


# ── GET /schemes ──────────────────────────────────────────────────────────────

@router.get("", response_model=SchemesListOut, summary="List all active government schemes")
async def list_schemes(
    category:    Optional[str] = Query(None, description="Filter by category"),
    sector:      Optional[str] = Query(None, description="Filter by sector"),
    state:       Optional[str] = Query(None, description="Filter by state applicability"),
    data_status: Optional[str] = Query(None, description="Filter by data_status: verified | demo"),
    db:          AsyncSession  = Depends(get_db),
) -> SchemesListOut:
    q = select(Scheme).where(Scheme.is_active == True)
    if category:    q = q.where(Scheme.category == category)
    if sector:      q = q.where(Scheme.sector   == sector)
    if data_status: q = q.where(Scheme.data_status == data_status)
    q = q.order_by(Scheme.sort_order)

    result = await db.execute(q)
    schemes = list(result.scalars().all())

    if state:
        state_l = state.lower().strip()
        schemes = [
            s for s in schemes
            if s.location_scope == "National"
               or state_l in [x.strip().lower() for x in s.states.split(",")]
               or "all" in [x.strip().lower() for x in s.states.split(",")]
        ]

    return SchemesListOut(items=[_to_summary(s) for s in schemes], total=len(schemes))


# ── GET /schemes/categories ───────────────────────────────────────────────────

@router.get("/categories", response_model=CategoriesOut, summary="Get available scheme categories and sectors")
async def get_categories(db: AsyncSession = Depends(get_db)) -> CategoriesOut:
    result = await db.execute(select(Scheme).where(Scheme.is_active == True))
    schemes = list(result.scalars().all())
    return CategoriesOut(
        categories = sorted(set(s.category for s in schemes)),
        sectors    = sorted(set(s.sector   for s in schemes)),
    )


# ── GET /schemes/{id} ────────────────────────────────────────────────────────

@router.get("/{scheme_id}", response_model=SchemeOut, summary="Get full details for a single scheme")
async def get_scheme(scheme_id: str, db: AsyncSession = Depends(get_db)) -> SchemeOut:
    result = await db.execute(select(Scheme).where(Scheme.id == scheme_id, Scheme.is_active == True))
    scheme = result.scalar_one_or_none()
    if not scheme:
        # Try by slug
        result = await db.execute(select(Scheme).where(Scheme.slug == scheme_id, Scheme.is_active == True))
        scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scheme '{scheme_id}' not found")
    return _to_full(scheme)


# ── POST /schemes/match ───────────────────────────────────────────────────────

@router.post("/match", response_model=MatchResultOut, summary="Match government schemes to your business and profile")
async def match_schemes_endpoint(
    body:         SchemeMatchRequest,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> MatchResultOut:
    """
    Intelligently match and rank government schemes based on:
      - Business type and category
      - Estimated investment vs available capital
      - User's state
      - User profile (age, gender, location type)
    """
    # Load business
    biz_result = await db.execute(select(Business).where(Business.id == body.business_id))
    biz = biz_result.scalar_one_or_none()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Business '{body.business_id}' not found")

    # Load all active schemes
    schemes = await _load_all_schemes(db)
    if not schemes:
        raise HTTPException(status_code=503, detail="Scheme database is empty. Please run the seed script.")

    # Build match request — supplement with user profile where available
    state = body.state or current_user.state
    req = MatchRequest(
        business_id          = biz.id,
        business_name        = biz.name,
        business_category    = biz.category,
        business_type        = biz.business_type,
        estimated_investment = body.estimated_investment,
        available_capital    = body.available_capital,
        state                = state,
        user_age             = body.user_age,
        is_woman             = body.is_woman,
        is_sc_st             = body.is_sc_st,
        is_rural             = body.is_rural,
    )

    result: MatchResult = match_schemes(schemes, req, top_n=10)

    return MatchResultOut(
        funding_gap   = FundingGapOut(**result.funding_gap.__dict__),
        matches       = [_match_to_out(m) for m in result.matches],
        best_overall  = result.best_overall,
        best_loan     = result.best_loan,
        best_subsidy  = result.best_subsidy,
        best_rural    = result.best_rural,
        total_schemes = len(result.matches),
        disclaimer    = DISCLAIMER,
    )


# ── POST /schemes/compare ────────────────────────────────────────────────────

@router.post("/compare", response_model=List[SchemeMatchOut], summary="Compare 2–4 specific government schemes")
async def compare_schemes_endpoint(
    body:         SchemeCompareRequest,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> List[SchemeMatchOut]:
    """
    Compare 2–4 specific schemes side-by-side.
    If business_id is provided, compute match scores; otherwise return neutral comparison.
    """
    if len(body.scheme_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 scheme IDs for comparison")
    if len(body.scheme_ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 schemes can be compared at once")

    schemes = await _load_all_schemes(db)

    req: Optional[MatchRequest] = None
    if body.business_id:
        biz_result = await db.execute(select(Business).where(Business.id == body.business_id))
        biz = biz_result.scalar_one_or_none()
        if biz and body.estimated_investment:
            req = MatchRequest(
                business_id          = biz.id,
                business_name        = biz.name,
                business_category    = biz.category,
                business_type        = biz.business_type,
                estimated_investment = body.estimated_investment,
                available_capital    = body.available_capital or 0,
                state                = body.state or current_user.state,
            )

    matches = compare_schemes(schemes, body.scheme_ids, req)
    if not matches:
        raise HTTPException(status_code=404, detail="None of the specified scheme IDs were found")

    return [_match_to_out(m) for m in matches]
