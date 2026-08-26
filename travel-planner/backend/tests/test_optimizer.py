from datetime import date

from app.models import Location
from app.services.catalog import poi
from app.services.optimizer import (
    days_and_daily_minutes,
    geographic_clusters,
    route_has_crossings,
    schedule_route,
    two_opt,
)


def candidate(identifier: str, lng: float, lat: float, minutes: int = 45):
    return poi(identifier, identifier, '自然风光', ('natural',), lng, lat, minutes, '全天开放', 'test')


def test_two_opt_removes_a_geometric_crossing():
    # A → B and C → D cross at the centre; the path is open, not a return tour.
    route = [
        candidate('A', 120.00, 30.00),
        candidate('B', 120.02, 30.02),
        candidate('C', 120.00, 30.02),
        candidate('D', 120.02, 30.00),
    ]
    assert route_has_crossings(route)
    optimized = two_opt(route)
    assert optimized[0].id == 'A'  # access-side start remains stable
    assert not route_has_crossings(optimized)


def test_geographic_kmeans_separates_regional_clusters():
    items = [
        candidate('west-1', 120.00, 30.00), candidate('west-2', 120.01, 30.01),
        candidate('east-1', 120.30, 30.20), candidate('east-2', 120.31, 30.21),
    ]
    clusters = geographic_clusters(items, 2)
    longitudes = [sum(item.location.lng for item in cluster) / len(cluster) for cluster in clusters]
    assert abs(longitudes[0] - longitudes[1]) > 0.15
    assert sorted(len(cluster) for cluster in clusters) == [2, 2]


def test_schedule_never_exceeds_daily_hard_limit_and_has_buffer():
    items = [
        candidate('A', 120.00, 30.00, 80),
        candidate('B', 120.01, 30.00, 80),
        candidate('C', 120.02, 30.00, 80),
    ]
    result = schedule_route(items, day_start_minute=9 * 60, daily_minutes=190, visit_date=date(2026, 8, 26))
    assert len(result.items) == 2
    assert result.items[-1].leave_minute <= 9 * 60 + 190
    assert result.total_buffer_minutes >= 15


def test_hours_duration_creates_short_final_day():
    days, budgets = days_and_daily_minutes(17, 'hours', 8)
    assert days == 3
    assert budgets == [480, 480, 60]
