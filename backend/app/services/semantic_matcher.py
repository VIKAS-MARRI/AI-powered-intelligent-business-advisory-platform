"""
Semantic Skill Matcher — Phase 8.

Performs intelligent semantic matching between user skills/interests and
business profiles WITHOUT requiring an internet connection or API key.

Approach:
1. Concept graph — hand-crafted synonyms/related concepts for rural Indian businesses
2. TF-IDF vector similarity using sklearn (if available)
3. Substring / token overlap as final fallback

Always returns results. Degrades gracefully: concept graph → sklearn → token overlap.
Returns similarity scores 0–100.
"""
from __future__ import annotations

import logging
import math
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Concept synonym graph ────────────────────────────────────────────────────
# Maps canonical concept → list of synonyms / related terms.
# When a user skill matches any term in a group, the canonical concept applies.

CONCEPT_GRAPH: Dict[str, List[str]] = {
    # Textiles / Clothing
    "tailoring":      ["stitching", "sewing", "garment", "clothing", "dress making", "alteration",
                       "embroidery", "fashion", "textile", "fabric", "cutting", "blouse", "uniform",
                       "kurta", "saree", "knitting", "weaving"],
    # Food
    "cooking":        ["food", "cooking", "chef", "baking", "bakery", "catering", "kitchen",
                       "snacks", "tiffin", "restaurant", "hotel", "idli", "dosa", "pickle",
                       "jam", "sweet", "mithai", "halwai", "papad", "spice"],
    # Electronics / Mobile
    "electronics":    ["mobile", "phone", "repair", "electronics", "circuit", "hardware",
                       "computer", "laptop", "appliance", "refrigerator", "television", "tv",
                       "inverter", "battery", "solar", "wiring", "electrical"],
    # Agriculture / Farming
    "farming":        ["agriculture", "farming", "crop", "paddy", "wheat", "vegetable",
                       "horticulture", "plant", "seed", "irrigation", "dairy", "cattle",
                       "goat", "poultry", "fish", "aquaculture", "mushroom", "organic"],
    # Trade / Retail
    "retail":         ["shop", "store", "trade", "sell", "vendor", "merchant", "kirana",
                       "grocery", "retail", "stationery", "hardware", "wholesale"],
    # Beauty / Grooming
    "beauty":         ["beauty", "salon", "parlour", "parlor", "grooming", "hair", "makeup",
                       "mehendi", "henna", "spa", "skincare", "cosmetology", "nail"],
    # Transport / Driving
    "transport":      ["driving", "transport", "vehicle", "auto", "truck", "delivery",
                       "logistics", "cab", "taxi", "rickshaw", "cargo", "courier"],
    # Construction / Carpentry
    "construction":   ["carpentry", "carpenter", "furniture", "woodwork", "masonry",
                       "plumbing", "construction", "welding", "fabrication", "painting",
                       "interior", "renovation", "tiles"],
    # Education / Training
    "education":      ["teaching", "tuition", "coaching", "training", "education",
                       "teacher", "instructor", "mentor", "school", "academy", "computer class"],
    # Healthcare / Medicine
    "healthcare":     ["healthcare", "medical", "nursing", "pharmacy", "medicine",
                       "ayurveda", "homeopathy", "first aid", "midwife", "health"],
    # Digital / IT
    "digital":        ["computer", "internet", "digital", "software", "programming",
                       "website", "data entry", "typing", "printing", "photocopy", "cyber"],
    # Animal husbandry
    "animal_care":    ["animal", "livestock", "veterinary", "vet", "cattle care", "dairy",
                       "husbandry", "goat", "poultry", "fish farming", "bee keeping", "honey"],
    # Handicrafts / Artisan
    "handicraft":     ["handicraft", "craft", "artisan", "pottery", "clay", "bamboo",
                       "basket", "weaving", "cane", "jute", "handloom", "embroidery",
                       "block printing", "tie-dye", "art", "painting"],
    # Finance / Accounting
    "finance":        ["accounting", "accounts", "finance", "bookkeeping", "tally",
                       "tax", "gst", "audit", "banking", "loan", "insurance", "agent"],
    # Marketing / Sales
    "sales":          ["sales", "marketing", "business development", "negotiation",
                       "customer", "client", "crm", "promotion", "advertising"],
    # Agro-processing / Value-add
    "agro_processing": ["processing", "value-add", "packaging", "grinding", "mill",
                        "flour", "rice mill", "oil expeller", "drying", "preservation",
                        "cold storage", "warehouse"],
}

# ── Business → concept mapping ────────────────────────────────────────────────
# Maps business keywords (in name/category/description) to relevant concepts.
# Used for scoring businesses against user concept profiles.

BUSINESS_CONCEPT_MAP: Dict[str, List[str]] = {
    "tailoring":        ["tailoring"],
    "boutique":         ["tailoring", "retail"],
    "garment":          ["tailoring", "retail"],
    "bakery":           ["cooking"],
    "dairy":            ["farming", "animal_care"],
    "poultry":          ["farming", "animal_care"],
    "goat farming":     ["farming", "animal_care"],
    "mushroom":         ["farming"],
    "vegetable":        ["farming", "retail"],
    "mobile repair":    ["electronics"],
    "electronics":      ["electronics"],
    "salon":            ["beauty"],
    "parlour":          ["beauty"],
    "transport":        ["transport"],
    "driving":          ["transport"],
    "carpentry":        ["construction"],
    "furniture":        ["construction", "retail"],
    "tuition":          ["education"],
    "coaching":         ["education"],
    "grocery":          ["retail"],
    "kirana":           ["retail"],
    "catering":         ["cooking"],
    "food":             ["cooking"],
    "fish":             ["farming", "animal_care"],
    "handicraft":       ["handicraft"],
    "pottery":          ["handicraft"],
    "weaving":          ["handicraft", "tailoring"],
    "digital":          ["digital"],
    "cyber":            ["digital"],
    "printing":         ["digital"],
    "agro":             ["agro_processing", "farming"],
    "processing":       ["agro_processing"],
    "medical":          ["healthcare"],
    "pharmacy":         ["healthcare", "retail"],
    "insurance":        ["finance", "sales"],
    "honey":            ["animal_care", "farming"],
}


# ── sklearn TF-IDF (optional) ─────────────────────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    _SKLEARN_AVAILABLE = True
    logger.info("sklearn available — using TF-IDF semantic matching")
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.info("sklearn not available — using concept-graph + token matching")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Lowercase, split on non-alpha, remove stop words."""
    STOP = {"a", "an", "the", "and", "or", "of", "in", "to", "for",
            "with", "my", "i", "have", "is", "are", "was", "be", "can"}
    tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
    return [t for t in tokens if t not in STOP]


def _text_to_concepts(text: str) -> Dict[str, float]:
    """Map free text → concept → match strength (0–1)."""
    tokens = _tokenize(text)
    text_lower = text.lower()
    concepts: Dict[str, float] = {}
    for concept, synonyms in CONCEPT_GRAPH.items():
        score = 0.0
        # Direct concept key match in text
        if concept.replace("_", " ") in text_lower or concept in tokens:
            score = max(score, 0.9)
        for syn in synonyms:
            syn_tokens = syn.split()
            # Phrase match
            if syn in text_lower:
                score = max(score, 1.0)
                continue
            # Token overlap
            matched = sum(1 for st in syn_tokens if st in tokens)
            score = max(score, matched / max(len(syn_tokens), 1))
        if score > 0.1:
            concepts[concept] = round(min(1.0, score), 3)
    return concepts


def _business_to_concepts(biz_text: str) -> Dict[str, float]:
    """Map business text → relevant concept strengths."""
    text_lower = biz_text.lower()
    concepts: Dict[str, float] = {}
    for keyword, related_concepts in BUSINESS_CONCEPT_MAP.items():
        if keyword in text_lower:
            for c in related_concepts:
                concepts[c] = max(concepts.get(c, 0.0), 0.8)
    # Also run through concept graph directly
    for concept, synonyms in CONCEPT_GRAPH.items():
        for syn in synonyms:
            if syn in text_lower:
                concepts[concept] = max(concepts.get(concept, 0.0), 0.6)
    return concepts


def _concept_overlap_score(user_concepts: Dict[str, float],
                            biz_concepts: Dict[str, float]) -> Tuple[float, List[str]]:
    """
    Cosine-style overlap between two concept vectors.
    Returns (score 0–100, list of matched concept names).
    """
    if not user_concepts or not biz_concepts:
        return 0.0, []

    matched = []
    dot = 0.0
    for concept, user_str in user_concepts.items():
        biz_str = biz_concepts.get(concept, 0.0)
        if biz_str > 0:
            dot += user_str * biz_str
            matched.append(concept)

    user_norm = math.sqrt(sum(v ** 2 for v in user_concepts.values()))
    biz_norm  = math.sqrt(sum(v ** 2 for v in biz_concepts.values()))
    denom = user_norm * biz_norm
    if denom == 0:
        return 0.0, []

    cosine = dot / denom
    return round(min(100.0, cosine * 100 * 1.4), 1), matched  # 1.4 boost for partial matches


def _tfidf_similarity(user_text: str, biz_text: str) -> float:
    """sklearn TF-IDF cosine similarity, 0–100."""
    if not _SKLEARN_AVAILABLE:
        return 0.0
    try:
        vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1)
        tfidf = vec.fit_transform([user_text, biz_text])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(sim) * 100, 1)
    except Exception:
        return 0.0


def _token_overlap_score(user_text: str, biz_text: str) -> float:
    """Simple token overlap score, 0–100."""
    user_tokens = set(_tokenize(user_text))
    biz_tokens  = set(_tokenize(biz_text))
    if not user_tokens or not biz_tokens:
        return 0.0
    overlap = user_tokens & biz_tokens
    score = len(overlap) / max(len(user_tokens), len(biz_tokens))
    return round(score * 100, 1)


# ── Main public API ───────────────────────────────────────────────────────────

def semantic_match(
    user_skills:    Optional[str],
    user_interests: Optional[str],
    biz_name:       str,
    biz_category:   str,
    biz_description: str,
    biz_required_skills: str,
) -> Dict:
    """
    Compute semantic similarity between a user profile and a business.

    Returns:
        {
          "semantic_score": float 0-100,
          "matched_concepts": [str, ...],
          "explanation": str,
          "method": str,
        }
    """
    if not user_skills and not user_interests:
        return {
            "semantic_score": 35.0,
            "matched_concepts": [],
            "explanation": "No skills or interests provided — neutral score applied.",
            "method": "default",
        }

    user_text = " ".join(filter(None, [user_skills, user_interests])).strip()
    biz_text  = " ".join(filter(None, [biz_name, biz_category, biz_description, biz_required_skills])).strip()

    # 1. Concept-graph matching (primary — always works)
    user_concepts = _text_to_concepts(user_text)
    biz_concepts  = _business_to_concepts(biz_text)
    concept_score, matched_concepts = _concept_overlap_score(user_concepts, biz_concepts)

    # 2. TF-IDF if sklearn available
    tfidf_score = _tfidf_similarity(user_text, biz_text)

    # 3. Token overlap fallback
    token_score = _token_overlap_score(user_text, biz_text)

    # Ensemble: concept graph (50%) + tfidf (35%) + token (15%)
    if _SKLEARN_AVAILABLE:
        final = round(concept_score * 0.50 + tfidf_score * 0.35 + token_score * 0.15, 1)
        method = "concept-graph + tfidf + token"
    else:
        final = round(concept_score * 0.70 + token_score * 0.30, 1)
        method = "concept-graph + token"

    # Direct word overlap bonus: when identical significant words appear in both texts
    user_words = set(_tokenize(user_text))
    biz_words  = set(_tokenize(biz_text))
    common_sig = {w for w in user_words & biz_words if len(w) >= 5}
    if common_sig:
        direct_bonus = min(30.0, len(common_sig) * 10.0)
        final = min(100.0, final + direct_bonus)

    final = min(100.0, max(0.0, final))

    # Generate explanation
    explanation = _build_explanation(final, matched_concepts, user_text, biz_name, user_concepts)

    return {
        "semantic_score":    round(final, 1),
        "matched_concepts":  matched_concepts,
        "explanation":       explanation,
        "method":            method,
        "component_scores": {
            "concept_graph": concept_score,
            "tfidf":         tfidf_score,
            "token_overlap": token_score,
        },
    }


def _build_explanation(score: float, matched: List[str], user_text: str,
                        biz_name: str, user_concepts: Dict[str, float]) -> str:
    """Generate a human-readable explanation for the semantic match."""
    if score >= 75:
        concept_str = ", ".join(matched[:3]) if matched else "your experience"
        return (f"Your background in {concept_str} strongly aligns with {biz_name}. "
                f"This business directly uses skills you already have.")
    elif score >= 50:
        if matched:
            concept_str = ", ".join(matched[:2])
            return (f"Your {concept_str} experience partially matches {biz_name}. "
                    f"Some upskilling may be beneficial.")
        return (f"Some skills from your profile apply to {biz_name}. "
                f"Additional training may be needed.")
    elif score >= 25:
        return (f"Limited skill overlap with {biz_name} detected. "
                f"This business may require learning new skills, but is not impossible.")
    else:
        return (f"Your stated skills have minimal direct overlap with {biz_name}. "
                f"This can still be a good opportunity if you are willing to learn.")


def batch_semantic_match(
    user_skills:    Optional[str],
    user_interests: Optional[str],
    businesses: List[Dict],   # each: {id, name, category, description, required_skills}
) -> List[Dict]:
    """
    Score a list of businesses semantically.
    Returns list sorted by semantic_score descending.
    """
    results = []
    for biz in businesses:
        result = semantic_match(
            user_skills      = user_skills,
            user_interests   = user_interests,
            biz_name         = biz.get("name", ""),
            biz_category     = biz.get("category", ""),
            biz_description  = biz.get("description", ""),
            biz_required_skills = biz.get("required_skills", ""),
        )
        results.append({
            "business_id":     biz.get("id"),
            "business_name":   biz.get("name"),
            **result,
        })
    results.sort(key=lambda x: x["semantic_score"], reverse=True)
    return results


def extract_query_intent(query: str) -> Dict:
    """
    Parse a natural-language query and extract:
    - budget (float or None)
    - skills (str)
    - risk_preference (str or None)
    - business_type_hints (list of str)
    - location_type (str or None)
    """
    q = query.lower()

    # Budget extraction — ₹ or Rs or rupees with common patterns
    budget = None
    # Match: ₹2L, ₹2 lakh, 2 lakh, Rs 50000, ₹50,000
    patterns = [
        r"\u20b9?\s*(\d+(?:\.\d+)?)\s*(?:lakh|l)\b",      # 2 lakh / 2L  
        r"(\d+(?:\.\d+)?)\s*(?:thousand|k)\b",             # 50k / 50 thousand (before rupee patterns)
        r"(?:rs\.?|\u20b9)\s*(\d[\d,]*)",                  # \u20b950,000 or Rs 50000
        r"(\d[\d,]{4,})\s*(?:rupees?|inr)",                # 200000 rupees (4+ digits)
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            raw     = m.group(1).replace(",", "")
            val     = float(raw)
            matched = m.group(0).lower()   # full matched string e.g. "50k" or "2 lakh"
            win     = q[max(0, m.start()-5):m.end()+12].lower()
            if "lakh" in matched or "lakh" in win or re.search(r"\bl\b", win):
                val *= 100000
            elif "thousand" in matched or "thousand" in win or \
                 "k" in matched or re.search(r"\bk\b", win):
                val *= 1000
            budget = val
            break

    # Skill extraction
    skill_markers = ["know", "expert in", "experience in", "i am good at",
                     "skilled in", "i do", "i have", "background in", "worked in"]
    skills = ""
    for marker in skill_markers:
        if marker in q:
            idx = q.index(marker) + len(marker)
            # take next 5–8 words
            snippet = " ".join(q[idx:idx+60].split()[:8])
            skills = snippet
            break
    if not skills:
        # concept-based extraction
        found_concepts = []
        for concept, synonyms in CONCEPT_GRAPH.items():
            for syn in synonyms:
                if syn in q:
                    found_concepts.append(concept)
                    break
        skills = ", ".join(found_concepts)

    # Risk preference
    risk = None
    if any(w in q for w in ["low risk", "safe", "stable", "secure"]):
        risk = "Low"
    elif any(w in q for w in ["high risk", "aggressive", "growth"]):
        risk = "High"
    elif any(w in q for w in ["moderate", "medium", "balanced"]):
        risk = "Medium"

    # Business type hints
    type_hints = []
    type_map = {
        "food": "Food", "farming": "Agriculture", "agriculture": "Agriculture",
        "retail": "Retail", "shop": "Retail", "service": "Service",
        "manufacturing": "Manufacturing", "digital": "Digital", "online": "Digital",
        "tailoring": "Manufacturing", "beauty": "Service", "salon": "Service",
    }
    for kw, btype in type_map.items():
        if kw in q and btype not in type_hints:
            type_hints.append(btype)

    # Location type
    location = None
    if any(w in q for w in ["rural", "village", "gram", "panchayat"]):
        location = "rural"
    elif any(w in q for w in ["urban", "city", "town"]):
        location = "urban"
    elif any(w in q for w in ["semi-urban", "tehsil", "taluk"]):
        location = "semi_urban"

    return {
        "budget":               budget,
        "skills":               skills,
        "risk_preference":      risk,
        "business_type_hints":  type_hints,
        "location_type":        location,
        "raw_query":            query,
    }
