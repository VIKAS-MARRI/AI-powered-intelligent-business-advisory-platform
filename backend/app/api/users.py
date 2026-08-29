"""
User profile endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.user import User
from app.schemas.user import UpdateProfileRequest, UserPublic

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserPublic, summary="Get current user profile")
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserPublic, summary="Update current user profile")
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Partially update the authenticated user's profile.
    Only fields provided in the request body are updated.
    """
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
