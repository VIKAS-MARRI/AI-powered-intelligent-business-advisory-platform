"""
Business catalog endpoints.
GET /businesses           — list with filters
GET /businesses/categories — list unique categories
GET /businesses/{id}      — single business
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.models.business import Business
from app.schemas.business import BusinessPublic, BusinessListResponse

router = APIRouter(prefix="/businesses", tags=["Businesses"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_public(b: Business) -> BusinessPublic:
    return BusinessPublic.from_orm_with_extras(b)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/categories",
    response_model=List[str],
    summary="List all business categories",
)
async def get_categories(db: AsyncSession = Depends(get_db)) -> List[str]:
    """Return a sorted list of unique business categories."""
    result = await db.execute(select(distinct(Business.category)).order_by(Business.category))
    return [row[0] for row in result.all()]


@router.get(
    "",
    response_model=BusinessListResponse,
    summary="List all businesses (with optional filters)",
)
async def list_businesses(
    category: Optional[str]   = Query(None, description="Filter by category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: Low / Medium / High"),
    min_inv: Optional[float]  = Query(None, alias="min_investment", description="Minimum investment ≤ this value"),
    max_inv: Optional[float]  = Query(None, alias="max_investment", description="Maximum investment ≥ this value"),
    rural_only: bool          = Query(False, description="Only show rural-suitable businesses"),
    search: Optional[str]     = Query(None, description="Search in name and description"),
    db: AsyncSession = Depends(get_db),
) -> BusinessListResponse:
    """
    Return all businesses, optionally filtered.
    Financial values are ESTIMATES for advisory purposes only.
    """
    stmt = select(Business)

    if category:
        stmt = stmt.where(Business.category == category)
    if risk_level:
        stmt = stmt.where(Business.risk_level == risk_level)
    if min_inv is not None:
        stmt = stmt.where(Business.min_investment <= min_inv)
    if max_inv is not None:
        stmt = stmt.where(Business.max_investment >= max_inv)
    if rural_only:
        stmt = stmt.where(Business.suitable_for_rural.is_(True))
    if search:
        kw = f"%{search}%"
        stmt = stmt.where(
            Business.name.ilike(kw) | Business.description.ilike(kw)
        )

    stmt = stmt.order_by(Business.category, Business.name)

    result = await db.execute(stmt)
    businesses = result.scalars().all()

    return BusinessListResponse(
        items=[_to_public(b) for b in businesses],
        total=len(businesses),
    )


@router.get(
    "/{business_id}",
    response_model=BusinessPublic,
    summary="Get a single business by ID",
)
async def get_business(
    business_id: str,
    db: AsyncSession = Depends(get_db),
) -> BusinessPublic:
    result = await db.execute(select(Business).where(Business.id == business_id))
    biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return _to_public(biz)
