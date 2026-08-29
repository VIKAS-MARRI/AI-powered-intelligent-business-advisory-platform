"""
Advisory API endpoints — Phase 7.

POST /advisor/query   — run the full multi-agent advisory workflow (JWT)
POST /advisor/analyze — alias for /query returning full structured results
GET  /advisor/status  — AI service health check (public)
GET  /advisor/history — user's past advisory sessions (JWT)
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import advisory_graph
from app.agents.prompts import DISCLAIMER
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.advisory import AdvisorySession
from app.models.user import User
from app.schemas.advisory import (
    AdvisoryHistoryItem,
    AdvisoryHistoryOut,
    AdvisoryQueryRequest,
    AdvisoryResultOut,
    AIStatusOut,
    FinalAdviceOut,
)
from app.services.ai_service import ai_service
from app.services.translation_service import get_translation_service
from app.core.languages import is_supported, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advisor", tags=["AI Advisor"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return "{}"


def _safe_json_loads(text: Optional[str]) -> Any:
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {}


def _make_final_advice_out(advice: Dict) -> FinalAdviceOut:
    return FinalAdviceOut(
        summary            = advice.get("summary", "Advisory complete."),
        recommendation     = advice.get("recommendation"),
        financial_plan     = advice.get("financial_plan"),
        market_insight     = advice.get("market_insight"),
        government_support = advice.get("government_support"),
        risks              = advice.get("risks", []),
        next_steps         = advice.get("next_steps", []),
        ai_generated       = advice.get("ai_generated", False),
        data_source        = advice.get("data_source"),
        disclaimer         = advice.get("disclaimer", DISCLAIMER),
        ai_generated_text  = advice.get("ai_generated_text"),
    )


async def _run_advisory(
    body: AdvisoryQueryRequest,
    current_user: User,
    db: AsyncSession,
) -> AdvisoryResultOut:
    """Core advisory workflow runner (shared by /query and /analyze)."""

    session_id = str(uuid.uuid4())

    # Build initial state; inject db session for agent use
    initial_state = {
        "user_id":           current_user.id,
        "question":          body.question.strip(),
        "available_capital": body.available_capital or current_user.available_capital,
        "business_id":       body.business_id,
        "latitude":          body.latitude,
        "longitude":         body.longitude,
        "state_name":        body.state_name or current_user.state,
        "radius_km":         body.radius_km or 5.0,
        "required_agents":   [],
        "business_result":   None,
        "finance_result":    None,
        "market_result":     None,
        "scheme_result":     None,
        "final_advice":      None,
        "ai_status":         ai_service.status,
        "errors":            [],
        "_db":               db,   # injected, not serialized
        # Phase 10 language metadata
        "language":          getattr(body, "language", None) or current_user.preferred_language or DEFAULT_LANGUAGE,
        "simple_language":   getattr(body, "simple_language", None) or bool(getattr(current_user, "simple_language_mode", False)),
    }

    # Phase 10: translate question to English if needed
    user_lang = initial_state.get("language", "en")
    original_question = initial_state["question"]
    canonical_question = original_question
    if user_lang != "en":
        try:
            tr = get_translation_service().translate_to_english(original_question, user_lang)
            canonical_question = tr.translated_text
            initial_state["question"] = canonical_question
        except Exception as te:
            logger.warning(f"Input translation failed: {te}")

    try:
        final_state = await advisory_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Advisory graph error: %s", exc)
        final_state = {
            **initial_state,
            "required_agents": ["business"],
            "final_advice": {
                "summary":    "Advisory system encountered an error.",
                "risks":      ["Please try again."],
                "next_steps": ["Contact support if the issue persists."],
                "disclaimer": DISCLAIMER,
            },
            "errors": [str(exc)],
        }

    # Remove non-serializable _db from state
    final_state.pop("_db", None)

    required_agents = final_state.get("required_agents", [])
    advice          = final_state.get("final_advice") or {}
    errors          = final_state.get("errors", [])
    ai_st           = final_state.get("ai_status", ai_service.status)

    results: Dict[str, Any] = {}
    for key in ("business_result", "finance_result", "market_result", "scheme_result"):
        val = final_state.get(key)
        if val:
            # Remove non-serializable fields
            clean = {k: v for k, v in val.items() if k != "_db"}
            results[key.replace("_result", "")] = clean

    # Persist session
    try:
        session = AdvisorySession(
            id               = session_id,
            user_id          = current_user.id,
            question         = original_question,
            available_capital= body.available_capital or current_user.available_capital,
            business_id      = body.business_id,
            latitude         = body.latitude,
            longitude        = body.longitude,
            state_name       = body.state_name or current_user.state,
            required_agents  = json.dumps(required_agents),
            business_result  = _safe_json_dumps(results.get("business")),
            finance_result   = _safe_json_dumps(results.get("finance")),
            market_result    = _safe_json_dumps(results.get("market")),
            scheme_result    = _safe_json_dumps(results.get("scheme")),
            final_advice     = _safe_json_dumps(advice),
            ai_status        = ai_st,
            status           = "completed" if not errors else "completed_with_errors",
            # Phase 10 language metadata
            original_language = user_lang,
            canonical_query   = canonical_question if user_lang != "en" else None,
            response_language = user_lang,
        )
        db.add(session)
        await db.commit()
    except Exception as exc:
        logger.warning("Could not persist advisory session: %s", exc)

    return AdvisoryResultOut(
        session_id      = session_id,
        status          = "success" if not errors else "partial",
        required_agents = required_agents,
        ai_status       = ai_st,
        results         = results,
        final_advice    = _make_final_advice_out(advice),
        errors          = errors,
        disclaimer      = DISCLAIMER,
    )


# ── POST /advisor/query ───────────────────────────────────────────────────────

@router.post("/query", response_model=AdvisoryResultOut,
             summary="Ask RuralBiz AI — full multi-agent advisory")
async def advisory_query(
    body:         AdvisoryQueryRequest,
    current_user: User            = Depends(get_current_user),
    db:           AsyncSession    = Depends(get_db),
) -> AdvisoryResultOut:
    """
    Run the full multi-agent advisory workflow.

    Supervisor determines which specialist agents (business, finance, market, scheme)
    are required, then synthesizes a personalized action plan.
    """
    return await _run_advisory(body, current_user, db)


# ── POST /advisor/analyze ─────────────────────────────────────────────────────

@router.post("/analyze", response_model=AdvisoryResultOut,
             summary="Structured advisory analysis (alias for /query)")
async def advisory_analyze(
    body:         AdvisoryQueryRequest,
    current_user: User            = Depends(get_current_user),
    db:           AsyncSession    = Depends(get_db),
) -> AdvisoryResultOut:
    """Returns the same structured result as /query, for API clarity."""
    return await _run_advisory(body, current_user, db)


# ── GET /advisor/status ───────────────────────────────────────────────────────

@router.get("/status", response_model=AIStatusOut,
            summary="AI service health check")
async def advisor_status() -> AIStatusOut:
    """
    Returns AI service availability.
    Does NOT expose API keys or secrets.
    """
    return AIStatusOut(
        ai_available       = ai_service.is_available(),
        provider           = "gemini",
        model              = settings.GEMINI_MODEL if ai_service.is_available() else "none",
        fallback_available = True,
        status             = ai_service.status,
    )


# ── GET /advisor/history ──────────────────────────────────────────────────────

@router.get("/history", response_model=AdvisoryHistoryOut,
            summary="Your past advisory sessions")
async def advisor_history(
    limit:        int          = Query(20, ge=1, le=100),
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> AdvisoryHistoryOut:
    """Returns the authenticated user's advisory session history."""
    result = await db.execute(
        select(AdvisorySession)
        .where(AdvisorySession.user_id == current_user.id)
        .order_by(AdvisorySession.created_at.desc())
        .limit(limit)
    )
    sessions = list(result.scalars().all())

    items = []
    for s in sessions:
        advice = _safe_json_loads(s.final_advice)
        items.append(AdvisoryHistoryItem(
            id              = s.id,
            question        = s.question,
            required_agents = json.loads(s.required_agents or "[]"),
            ai_status       = s.ai_status,
            status          = s.status,
            created_at      = s.created_at,
            summary         = advice.get("summary"),
        ))

    return AdvisoryHistoryOut(items=items, total=len(items))
