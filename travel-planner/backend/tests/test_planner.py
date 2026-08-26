import pytest

from app.config import Settings
from app.models import Duration, TravelRequest
from app.services.optimizer import route_has_crossings
from app.services.planner import PlanningService


@pytest.mark.asyncio
async def test_plan_response_honours_route_invariants_without_amap_key():
    service = PlanningService(Settings(amap_web_service_key=None))
    response = await service.plan(TravelRequest(
        destination='杭州',
        duration=Duration(value=3, unit='days'),
        preferences=['natural', 'culture', 'food', 'museum'],
        daily_hours=8,
    ))
    assert response.total_days == 3
    assert response.overall_stats.backtrack_check == 'passed'
    assert response.overall_stats.total_spots > 0
    assert all(len(route.spots) <= 6 for route in response.routes)
    # The public route only contains POI models, so test coordinate path crossings directly.
    for route in response.routes:
        seen = set()
        coordinates = []
        for spot in route.spots:
            assert spot.id not in seen
            seen.add(spot.id)
            coordinates.append(spot.location)
        # A compact generic geometry check for output edges.
        for first in range(len(coordinates) - 1):
            for second in range(first + 2, len(coordinates) - 1):
                from app.services.optimizer import segments_intersect
                assert not segments_intersect(coordinates[first], coordinates[first + 1], coordinates[second], coordinates[second + 1])
