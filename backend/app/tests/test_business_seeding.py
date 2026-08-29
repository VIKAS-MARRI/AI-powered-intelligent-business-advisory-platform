from unittest.mock import AsyncMock, patch

import pytest

from app.seed_businesses import seed_businesses


@pytest.mark.asyncio
async def test_seed_businesses_does_not_reenter_init_db():
    """Seeder should not call init_db() itself; startup already initializes the DB."""
    session = AsyncMock()
    result = AsyncMock()
    result.scalar_one_or_none = AsyncMock(return_value=None)
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()

    with patch(
        "app.seed_businesses.init_db",
        new=AsyncMock(side_effect=AssertionError("seed_businesses must not call init_db()")),
    ):
        with patch("app.seed_businesses.AsyncSessionLocal") as session_factory:
            session_factory.return_value.__aenter__.return_value = session
            session_factory.return_value.__aexit__.return_value = None

            result = await seed_businesses()

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] >= 0
    assert result[1] >= 0
