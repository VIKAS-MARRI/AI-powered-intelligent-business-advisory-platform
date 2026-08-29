"""
Comprehensive unit tests for Phase 5 Market Intelligence.

All external HTTP calls (Nominatim + Overpass) are mocked so tests run
fully offline and never depend on live APIs.

Run with: python -m pytest app/tests/test_market_intelligence.py -v
"""
import sys
import math
import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# ── Service imports ─────────────────────────────────────────────────────────
from app.services.location_service import (
    validate_coordinates,
    haversine_distance,
    radius_km_to_degrees,
    search_location,
    reverse_geocode,
)
from app.services.overpass_service import (
    NearbyPlace,
    OverpassResult,
    _classify_osm_tags,
    _extract_name,
    _element_to_place,
    _cache_key,
    _cache_get,
    _cache_set,
    _competitor_tag_filters,
    _build_overpass_query,
    fetch_nearby_places,
    fetch_competitors,
    clear_cache,
    CACHE_TTL_SECONDS,
)
from app.services.market_analyzer import (
    analyse_market,
    _competition_level,
    _score_opportunity,
    _score_suitability,
    _generate_insights,
    _generate_recommendations,
    _area_sqkm,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

VALID_LAT   =  18.5
VALID_LON   =  79.5
RADIUS_KM   =  5.0
BIZ_NAME    = "Tailoring & Boutique"
BIZ_ID      = "biz-t01"


def _make_place(name="Shop A", cat="Retail", dist=200.0) -> NearbyPlace:
    return NearbyPlace(
        osm_id="node/1", name=name, category=cat,
        osm_tags={"shop": "general"}, latitude=18.502,
        longitude=79.502, distance_meters=dist,
    )


def _make_overpass_node(osm_id=1, lat=18.502, lon=79.502, tags=None):
    return {"type": "node", "id": osm_id, "lat": lat, "lon": lon, "tags": tags or {"shop": "general", "name": "Test Shop"}}


def _sample_overpass_response(elements=None):
    return {"elements": elements or [_make_overpass_node()]}


# ══════════════════════════════════════════════════════════════════════════════
# TestCoordinateValidation
# ══════════════════════════════════════════════════════════════════════════════

class TestCoordinateValidation:
    def test_valid_coordinates(self):
        validate_coordinates(18.5, 79.5)   # should not raise

    def test_invalid_latitude_high(self):
        with pytest.raises(ValueError):
            validate_coordinates(91.0, 0.0)

    def test_invalid_latitude_low(self):
        with pytest.raises(ValueError):
            validate_coordinates(-91.0, 0.0)

    def test_invalid_longitude_high(self):
        with pytest.raises(ValueError):
            validate_coordinates(0.0, 181.0)

    def test_invalid_longitude_low(self):
        with pytest.raises(ValueError):
            validate_coordinates(0.0, -181.0)

    def test_edge_latitude_90(self):
        validate_coordinates(90.0, 0.0)

    def test_edge_longitude_180(self):
        validate_coordinates(0.0, 180.0)

    def test_zero_coordinates(self):
        validate_coordinates(0.0, 0.0)


# ══════════════════════════════════════════════════════════════════════════════
# TestHaversineDistance
# ══════════════════════════════════════════════════════════════════════════════

class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(18.5, 79.5, 18.5, 79.5) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance(self):
        # Approx 1 degree latitude ≈ 111 km
        d = haversine_distance(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 112_000

    def test_symmetry(self):
        d1 = haversine_distance(18.5, 79.5, 19.0, 80.0)
        d2 = haversine_distance(19.0, 80.0, 18.5, 79.5)
        assert abs(d1 - d2) < 1.0

    def test_result_in_metres(self):
        # Two points ~5 km apart
        d = haversine_distance(18.5, 79.5, 18.545, 79.5)
        assert 4_000 < d < 6_000


# ══════════════════════════════════════════════════════════════════════════════
# TestOSMTagClassification
# ══════════════════════════════════════════════════════════════════════════════

class TestOSMTagClassification:
    def test_dairy_shop(self):
        assert _classify_osm_tags({"shop": "dairy"}) == "Dairy & Milk"

    def test_tailor_craft(self):
        assert _classify_osm_tags({"craft": "tailor"}) == "Tailoring & Clothing"

    def test_supermarket(self):
        assert _classify_osm_tags({"shop": "supermarket"}) == "Retail & Distribution"

    def test_pharmacy(self):
        assert _classify_osm_tags({"amenity": "pharmacy"}) == "Medical & Health"

    def test_marketplace(self):
        assert _classify_osm_tags({"amenity": "marketplace"}) == "Market"

    def test_unknown_shop_tag(self):
        # Falls back to generic "Retail"
        result = _classify_osm_tags({"shop": "xyz_unknown_type"})
        assert result == "Retail"

    def test_empty_tags(self):
        result = _classify_osm_tags({})
        assert result == "Other"

    def test_transport(self):
        assert _classify_osm_tags({"amenity": "bus_station"}) == "Transport"

    def test_education(self):
        assert _classify_osm_tags({"amenity": "school"}) == "Education"


# ══════════════════════════════════════════════════════════════════════════════
# TestExtractName
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractName:
    def test_name_tag(self):
        assert _extract_name({"name": "Sharma Dairy"}) == "Sharma Dairy"

    def test_name_en_fallback(self):
        assert _extract_name({"name:en": "Corner Shop"}) == "Corner Shop"

    def test_brand_fallback(self):
        assert _extract_name({"brand": "RelIance"}) == "RelIance"

    def test_unnamed_fallback(self):
        assert _extract_name({}) == "Unnamed"

    def test_name_takes_priority(self):
        assert _extract_name({"name": "A", "brand": "B"}) == "A"


# ══════════════════════════════════════════════════════════════════════════════
# TestElementToPlace
# ══════════════════════════════════════════════════════════════════════════════

class TestElementToPlace:
    def test_node_element(self):
        el = _make_overpass_node(lat=18.505, lon=79.505, tags={"shop": "dairy", "name": "Milk Corner"})
        place = _element_to_place(el, VALID_LAT, VALID_LON)
        assert place is not None
        assert place.name == "Milk Corner"
        assert place.category == "Dairy & Milk"
        assert place.distance_meters > 0

    def test_element_without_tags_returns_none(self):
        el = {"type": "node", "id": 1, "lat": 18.5, "lon": 79.5, "tags": {}}
        assert _element_to_place(el, VALID_LAT, VALID_LON) is None

    def test_way_element_uses_center(self):
        el = {
            "type": "way", "id": 2,
            "center": {"lat": 18.501, "lon": 79.501},
            "tags": {"amenity": "marketplace", "name": "Manthani Market"},
        }
        place = _element_to_place(el, VALID_LAT, VALID_LON)
        assert place is not None
        assert place.category == "Market"

    def test_way_element_without_center_returns_none(self):
        el = {"type": "way", "id": 3, "tags": {"shop": "general"}}
        assert _element_to_place(el, VALID_LAT, VALID_LON) is None

    def test_distance_is_calculated(self):
        el = _make_overpass_node(lat=18.505, lon=79.505)
        place = _element_to_place(el, VALID_LAT, VALID_LON)
        expected = haversine_distance(VALID_LAT, VALID_LON, 18.505, 79.505)
        assert abs(place.distance_meters - expected) < 1.0


# ══════════════════════════════════════════════════════════════════════════════
# TestCompetitorTagFilters
# ══════════════════════════════════════════════════════════════════════════════

class TestCompetitorTagFilters:
    def test_tailoring_matches(self):
        filters = _competitor_tag_filters("Tailoring & Boutique")
        assert len(filters) > 0

    def test_dairy_matches(self):
        filters = _competitor_tag_filters("Dairy Farming")
        assert len(filters) > 0

    def test_kirana_matches(self):
        filters = _competitor_tag_filters("Kirana Store")
        assert len(filters) > 0

    def test_unknown_business_returns_empty(self):
        filters = _competitor_tag_filters("Completely Unknown Business Type XYZ")
        assert filters == []

    def test_no_duplicate_filters(self):
        filters = _competitor_tag_filters("Tailoring & Clothing Shop")
        assert len(filters) == len(set(filters))


# ══════════════════════════════════════════════════════════════════════════════
# TestCache
# ══════════════════════════════════════════════════════════════════════════════

class TestCache:
    def setup_method(self):
        clear_cache()

    def test_cache_miss_returns_none(self):
        key = _cache_key(18.5, 79.5, 5.0, "test")
        assert _cache_get(key) is None

    def test_cache_set_and_get(self):
        key    = _cache_key(18.5, 79.5, 5.0, "test2")
        result = OverpassResult(places=[_make_place()])
        _cache_set(key, result)
        cached = _cache_get(key)
        assert cached is not None
        assert cached.from_cache is True

    def test_cache_key_rounds_coordinates(self):
        k1 = _cache_key(18.5001, 79.5001, 5.0, "q")
        k2 = _cache_key(18.5002, 79.5002, 5.0, "q")
        # Should be the same after rounding to 3dp
        assert k1 == k2

    def test_expired_cache_returns_none(self):
        import app.services.overpass_service as svc
        key    = _cache_key(18.5, 79.5, 5.0, "exp")
        result = OverpassResult(places=[])
        # Manually set with already-expired time
        svc._cache[key] = (time.time() - 1, result)
        assert _cache_get(key) is None

    def test_clear_cache(self):
        key = _cache_key(18.5, 79.5, 5.0, "clr")
        _cache_set(key, OverpassResult())
        clear_cache()
        assert _cache_get(key) is None


# ══════════════════════════════════════════════════════════════════════════════
# TestFetchNearbyPlaces (mocked HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestFetchNearbyPlaces:
    def setup_method(self):
        clear_cache()

    @pytest.mark.asyncio
    async def test_normal_response(self):
        elements = [
            _make_overpass_node(1, 18.502, 79.502, {"shop": "dairy", "name": "A"}),
            _make_overpass_node(2, 18.503, 79.503, {"amenity": "marketplace", "name": "B"}),
        ]
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, return_value={"elements": elements}):
            result = await fetch_nearby_places(VALID_LAT, VALID_LON, RADIUS_KM)
        assert result.error is None
        assert len(result.places) == 2

    @pytest.mark.asyncio
    async def test_empty_overpass_response(self):
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, return_value={"elements": []}):
            result = await fetch_nearby_places(VALID_LAT, VALID_LON, RADIUS_KM)
        assert result.error is None
        assert result.places == []

    @pytest.mark.asyncio
    async def test_overpass_timeout(self):
        import httpx
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, side_effect=httpx.TimeoutException("timeout")):
            result = await fetch_nearby_places(VALID_LAT, VALID_LON, RADIUS_KM)
        assert result.error is not None
        assert "timed out" in result.error.lower()
        assert result.places == []

    @pytest.mark.asyncio
    async def test_overpass_generic_error(self):
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, side_effect=Exception("connection refused")):
            result = await fetch_nearby_places(VALID_LAT, VALID_LON, RADIUS_KM)
        assert result.error is not None
        assert result.places == []

    @pytest.mark.asyncio
    async def test_results_cached(self):
        clear_cache()
        elements = [_make_overpass_node()]
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, return_value={"elements": elements}) as mock_q:
            await fetch_nearby_places(VALID_LAT, VALID_LON, RADIUS_KM)
            await fetch_nearby_places(VALID_LAT, VALID_LON, RADIUS_KM)
        # Second call should use cache — query called only once
        assert mock_q.call_count == 1

    @pytest.mark.asyncio
    async def test_invalid_coordinates_raise(self):
        with pytest.raises(ValueError):
            await fetch_nearby_places(999.0, 79.5, RADIUS_KM)


# ══════════════════════════════════════════════════════════════════════════════
# TestFetchCompetitors (mocked HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestFetchCompetitors:
    def setup_method(self):
        clear_cache()

    @pytest.mark.asyncio
    async def test_tailoring_competitors(self):
        elements = [_make_overpass_node(1, 18.501, 79.501, {"shop": "tailor", "name": "Rama Tailors"})]
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, return_value={"elements": elements}):
            result = await fetch_competitors(VALID_LAT, VALID_LON, "Tailoring Business", RADIUS_KM)
        assert result.error is None
        assert len(result.places) == 1

    @pytest.mark.asyncio
    async def test_no_mapping_returns_empty(self):
        result = await fetch_competitors(VALID_LAT, VALID_LON, "Unknown XYZ Business", RADIUS_KM)
        assert result.places == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_competitors_timeout(self):
        import httpx
        with patch("app.services.overpass_service._overpass_query",
                   new_callable=AsyncMock, side_effect=httpx.TimeoutException("timed out")):
            result = await fetch_competitors(VALID_LAT, VALID_LON, "Dairy Farming", RADIUS_KM)
        assert result.error is not None
        assert result.places == []


# ══════════════════════════════════════════════════════════════════════════════
# TestCompetitionLevel
# ══════════════════════════════════════════════════════════════════════════════

class TestCompetitionLevel:
    def test_zero_competitors_is_low(self):
        assert _competition_level(0, 5.0) == "Low"

    def test_low_density_is_low(self):
        # area = π * 25 ≈ 78.5 km²; 1 / 78.5 ≈ 0.013 / km² → Low
        assert _competition_level(1, 5.0) == "Low"

    def test_moderate_density(self):
        # Need ~40–160 competitors in 5 km radius for moderate (0.5–2 per km²)
        # 80 / 78.5 ≈ 1.02 → Moderate
        assert _competition_level(80, 5.0) == "Moderate"

    def test_high_density(self):
        # 200 / 78.5 ≈ 2.55 → High
        assert _competition_level(200, 5.0) == "High"

    def test_smaller_radius_higher_density(self):
        # Same count, smaller area → higher density
        level_small = _competition_level(5, 1.0)   # area=3.14 → 1.59 → Moderate+
        level_large = _competition_level(5, 10.0)  # area=314 → 0.016 → Low
        order = {"Low": 0, "Moderate": 1, "High": 2}
        assert order[level_small] >= order[level_large]


# ══════════════════════════════════════════════════════════════════════════════
# TestMarketOpportunityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestMarketOpportunityScore:
    def _places(self, cats: dict) -> list:
        places = []
        for cat, count in cats.items():
            for i in range(count):
                p = _make_place(cat=cat)
                places.append(p)
        return places

    def test_low_competition_high_score(self):
        places = self._places({"Market": 2, "Transport": 3, "Education": 2})
        score = _score_opportunity(0, places, 5.0)
        assert score.competition_score == pytest.approx(30.0, abs=0.5)
        assert score.total >= 50.0

    def test_high_competition_lower_competition_score(self):
        score_low = _score_opportunity(0, [], 5.0)
        score_high = _score_opportunity(20, [], 5.0)
        assert score_low.competition_score > score_high.competition_score

    def test_score_in_range(self):
        places = self._places({"Retail": 10, "Market": 2})
        score = _score_opportunity(3, places, 5.0)
        assert 0 <= score.total <= 100

    def test_infrastructure_bonus(self):
        with_infra    = self._places({"Market": 2, "Banking & Finance": 1, "Transport": 2})
        without_infra = self._places({"Retail": 5})
        s_with    = _score_opportunity(0, with_infra, 5.0)
        s_without = _score_opportunity(0, without_infra, 5.0)
        assert s_with.infrastructure_score > s_without.infrastructure_score

    def test_total_is_sum_of_subscores(self):
        places = self._places({"Market": 1})
        s = _score_opportunity(2, places, 5.0)
        expected = s.competition_score + s.infrastructure_score + s.accessibility_score + s.diversity_score + s.market_size_score
        assert abs(s.total - min(100.0, round(expected, 1))) < 1.0


# ══════════════════════════════════════════════════════════════════════════════
# TestLocationSuitabilityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestLocationSuitabilityScore:
    def _places(self, cats: dict) -> list:
        return [_make_place(cat=cat) for cat, n in cats.items() for _ in range(n)]

    def test_score_in_range(self):
        places = self._places({"Transport": 2, "Education": 1})
        score = _score_suitability(1, places, 5.0)
        assert 0 <= score.total <= 100

    def test_customer_proxy_increases_score(self):
        with_proxy    = self._places({"Education": 2, "Market": 2, "Transport": 1})
        without_proxy = self._places({"Retail": 5})
        s_with    = _score_suitability(0, with_proxy, 5.0)
        s_without = _score_suitability(0, without_proxy, 5.0)
        assert s_with.customer_proxy_score > s_without.customer_proxy_score

    def test_different_from_opportunity(self):
        """Suitability and Opportunity emphasise different factors."""
        places = self._places({"Education": 3, "Medical & Health": 2, "Market": 2})
        opp  = _score_opportunity(0, places, 5.0)
        suit = _score_suitability(0, places, 5.0)
        # They won't be equal because weights differ
        assert opp.total != suit.total or opp.infrastructure_score != suit.infrastructure_score


# ══════════════════════════════════════════════════════════════════════════════
# TestMarketAnalysis (end-to-end with mocked places)
# ══════════════════════════════════════════════════════════════════════════════

class TestMarketAnalysis:
    def _run(self, all_places, competitors):
        return analyse_market(
            latitude=VALID_LAT, longitude=VALID_LON,
            radius_km=RADIUS_KM,
            business_id=BIZ_ID, business_name=BIZ_NAME,
            all_places=all_places, competitors=competitors,
        )

    def test_low_competition_positive_insights(self):
        result = self._run(all_places=[], competitors=[])
        assert any(i.level == "positive" for i in result.insights)

    def test_high_competition_warning_insights(self):
        competitors = [_make_place(cat="Tailoring & Clothing") for _ in range(25)]
        result = self._run(all_places=competitors, competitors=competitors)
        assert any(i.level == "warning" for i in result.insights)

    def test_recommendations_not_empty(self):
        result = self._run([], [])
        assert len(result.recommendations) > 0

    def test_disclaimer_present(self):
        result = self._run([], [])
        assert "OpenStreetMap" in result.disclaimer

    def test_competitor_summary_correct(self):
        competitors = [_make_place() for _ in range(5)]
        result = self._run(all_places=competitors, competitors=competitors)
        assert result.competitor_summary.direct_count == 5

    def test_business_info_preserved(self):
        result = self._run([], [])
        assert result.business_id == BIZ_ID
        assert result.business_name == BIZ_NAME


# ══════════════════════════════════════════════════════════════════════════════
# TestLocationSearch (mocked HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestLocationSearch:
    NOMINATIM_RESPONSE = [
        {
            "place_id": 12345,
            "display_name": "Manthani, Peddapalli, Telangana, India",
            "lat": "18.65",
            "lon": "79.67",
            "osm_type": "node",
            "address": {
                "state": "Telangana",
                "county": "Peddapalli",
                "country": "India",
            },
        }
    ]

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        with patch("app.services.location_service._nominatim_search",
                   new_callable=AsyncMock, return_value=self.NOMINATIM_RESPONSE):
            results = await search_location("Manthani Telangana")
        assert len(results) == 1
        assert results[0].latitude == pytest.approx(18.65)
        assert "Manthani" in results[0].display_name

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self):
        results = await search_location("")
        assert results == []

    @pytest.mark.asyncio
    async def test_short_query_returns_empty(self):
        results = await search_location("a")
        assert results == []

    @pytest.mark.asyncio
    async def test_api_error_returns_empty(self):
        with patch("app.services.location_service._nominatim_search",
                   new_callable=AsyncMock, side_effect=Exception("network error")):
            results = await search_location("Some Place")
        assert results == []

    @pytest.mark.asyncio
    async def test_reverse_geocode_returns_result(self):
        with patch("app.services.location_service._nominatim_reverse",
                   new_callable=AsyncMock, return_value=self.NOMINATIM_RESPONSE[0]):
            result = await reverse_geocode(18.65, 79.67)
        assert result is not None
        assert result.latitude == pytest.approx(18.65)

    @pytest.mark.asyncio
    async def test_reverse_geocode_invalid_coords(self):
        result = await reverse_geocode(999.0, 79.5)
        assert result is None

    @pytest.mark.asyncio
    async def test_reverse_geocode_error_returns_none(self):
        with patch("app.services.location_service._nominatim_reverse",
                   new_callable=AsyncMock, side_effect=Exception("error")):
            result = await reverse_geocode(18.5, 79.5)
        assert result is None
