"""
Phase 10 — Language & Translation API.

Endpoints:
  GET  /languages                  — list supported languages (public)
  GET  /languages/supported        — same as above
  GET  /users/language             — get user's language preference (JWT)
  PATCH /users/language            — update user's language preference (JWT)
  GET  /users/accessibility        — get accessibility preferences (JWT)
  PATCH /users/accessibility       — update accessibility preferences (JWT)
  POST /language/translate         — translate text (JWT or public)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.languages import SUPPORTED_CODES, get_all_languages, is_supported
from app.database.db import get_db
from app.models.user import User
from app.services.translation_service import get_translation_service

# ── Routers ───────────────────────────────────────────────────────────────────
languages_router    = APIRouter(prefix="/languages",   tags=["Phase 10 — Languages"])
lang_user_router    = APIRouter(prefix="/users",       tags=["Phase 10 — User Language"])
translate_router    = APIRouter(prefix="/language",    tags=["Phase 10 — Translation"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LanguageUpdate(BaseModel):
    language: str = Field(..., description="Language code: en | hi | te")


class AccessibilityUpdate(BaseModel):
    simple_language_mode: bool = Field(...)


class TranslateRequest(BaseModel):
    text:            str  = Field(..., min_length=1, max_length=5000)
    target_language: str  = Field(...)
    source_language: str  = Field("en")


# ── Language list endpoints ───────────────────────────────────────────────────

@languages_router.get("", summary="List all supported languages")
async def list_languages():
    return {"languages": get_all_languages(), "default": "en"}


@languages_router.get("/supported", summary="Supported language codes")
async def supported_languages():
    return {"supported": SUPPORTED_CODES, "count": len(SUPPORTED_CODES)}


# ── User language preference ──────────────────────────────────────────────────

@lang_user_router.get("/language", summary="Get user language preference")
async def get_language(current_user: User = Depends(get_current_user)):
    return {
        "language":           current_user.preferred_language or "en",
        "supported_languages": get_all_languages(),
    }


@lang_user_router.patch("/language", summary="Update user language preference")
async def update_language(
    body:         LanguageUpdate,
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    if not is_supported(body.language):
        raise HTTPException(422, f"Unsupported language '{body.language}'. Supported: {SUPPORTED_CODES}")
    current_user.preferred_language = body.language
    db.add(current_user)
    await db.commit()
    return {"language": body.language, "message": "Language preference updated."}


# ── Accessibility preferences ─────────────────────────────────────────────────

@lang_user_router.get("/accessibility", summary="Get accessibility preferences")
async def get_accessibility(current_user: User = Depends(get_current_user)):
    return {
        "simple_language_mode": getattr(current_user, "simple_language_mode", False) or False,
        "preferred_language":   current_user.preferred_language or "en",
    }


@lang_user_router.patch("/accessibility", summary="Update accessibility preferences")
async def update_accessibility(
    body:         AccessibilityUpdate,
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    current_user.simple_language_mode = body.simple_language_mode
    db.add(current_user)
    await db.commit()
    return {
        "simple_language_mode": body.simple_language_mode,
        "message": "Accessibility preference updated.",
    }


# ── Translation endpoint ──────────────────────────────────────────────────────

@translate_router.post("/translate", summary="Translate text")
async def translate_text_endpoint(body: TranslateRequest):
    if not is_supported(body.target_language):
        raise HTTPException(422, f"Unsupported target language: {body.target_language}")
    svc = get_translation_service()
    result = svc.translate(
        text=body.text,
        target_language=body.target_language,
        source_language=body.source_language,
    )
    return result.to_dict()
