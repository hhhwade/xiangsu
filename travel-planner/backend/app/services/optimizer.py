"""Deterministic route optimization primitives.

The planner deliberately optimizes an *open* path (there is no implicit return to the
first POI).  This matches a traveller moving through a city and is key to preventing
artificial backtracking.  A production matrix can supply road-time metrics; geometric
checks remain independent so a traffic detour cannot accidentally introduce a
self-crossing display path.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Callable, Iterable, Mapping, Sequence, TypeVar

from app.models import Location
from app.services.catalog import CandidatePoi

T = TypeVar('T', bound=CandidatePoi)


@dataclass(frozen=True)
class TravelMetric:
    distance_km: float
    duration_minutes: int
    source: str = 'estimate'


@dataclass(frozen=True)
class ScheduledItem:
    poi: CandidatePoi
    arrival_minute: int
    leave_minute: int


@dataclass
class ScheduleResult:
    items: list[ScheduledItem]
    skipped: list[CandidatePoi]
    total_travel_minutes: int
    total_distance_km: float
    total_visit_minutes: int
    total_buffer_minutes: int
    notices: list[str]


EARTH_RADIUS_KM = 6371.0088
BUFFER_MINUTES = 15


def haversine_km(first: Location, second: Location) -> float:
    """Great-circle fallback suitable for cache/API degradation mode."""
    d_lat = radians(second.lat - first.lat)
    d_lng = radians(second.lng - first.lng)
    a = sin(d_lat / 2) ** 2 + cos(radians(first.lat)) * cos(radians(second.lat)) * sin(d_lng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def estimated_metric(first: CandidatePoi, second: CandidatePoi, mode: str = 'driving') -> TravelMetric:
    distance = haversine_km(first.location, second.location)
    # Straight-line distance is corrected to a conservative urban-road estimate.
    road_distance = distance * {'walking': 1.12, 'riding': 1.18, 'driving': 1.28, 'transit': 1.35}.get(mode, 1.28)
    km_per_hour = {'walking': 4.5, 'riding': 12.0, 'driving': 25.0, 'transit': 18.0}.get(mode, 25.0)
    base_wait = {'walking': 0, 'riding': 1, 'driving': 3, 'transit': 8}.get(mode, 3)
    duration = max(3, round(road_distance / km_per_hour * 60 + base_wait))
    return TravelMetric(distance_km=round(road_distance, 2), duration_minutes=duration)


def matrix_metric(
    first: CandidatePoi,
    second: CandidatePoi,
    matrix: Mapping[tuple[str, str], TravelMetric] | None,
    mode: str,
) -> TravelMetric:
    if matrix:
        metric = matrix.get((first.id, second.id))
        if metric:
            return metric
    return estimated_metric(first, second, mode)


def _orientation(a: Location, b: Location, c: Location) -> float:
    return (b.lng - a.lng) * (c.lat - a.lat) - (b.lat - a.lat) * (c.lng - a.lng)


def _on_segment(a: Location, b: Location, point: Location) -> bool:
    return (
        min(a.lng, b.lng) - 1e-10 <= point.lng <= max(a.lng, b.lng) + 1e-10
        and min(a.lat, b.lat) - 1e-10 <= point.lat <= max(a.lat, b.lat) + 1e-10
    )


def segments_intersect(a: Location, b: Location, c: Location, d: Location) -> bool:
    """True for crossings or collinear overlaps between independent segments."""
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    epsilon = 1e-10
    if ((o1 > epsilon and o2 < -epsilon) or (o1 < -epsilon and o2 > epsilon)) and ((o3 > epsilon and o4 < -epsilon) or (o3 < -epsilon and o4 > epsilon)):
        return True
    if abs(o1) <= epsilon and _on_segment(a, b, c):
        return True
    if abs(o2) <= epsilon and _on_segment(a, b, d):
        return True
    if abs(o3) <= epsilon and _on_segment(c, d, a):
        return True
    if abs(o4) <= epsilon and _on_segment(c, d, b):
        return True
    return False


def route_has_crossings(route: Sequence[CandidatePoi]) -> bool:
    for edge_index in range(len(route) - 1):
        for other_index in range(edge_index + 2, len(route) - 1):
            # Open paths only: adjacent segments share a valid endpoint and are skipped.
            if segments_intersect(
                route[edge_index].location,
                route[edge_index + 1].location,
                route[other_index].location,
                route[other_index + 1].location,
            ):
                return True
    return False


def path_distance(
    route: Sequence[CandidatePoi], matrix: Mapping[tuple[str, str], TravelMetric] | None = None,
    mode: str = 'driving',
) -> float:
    return sum(matrix_metric(a, b, matrix, mode).distance_km for a, b in zip(route, route[1:]))


def nearest_neighbor(
    items: Sequence[CandidatePoi], *, start: Location | None = None,
    matrix: Mapping[tuple[str, str], TravelMetric] | None = None, mode: str = 'driving',
) -> list[CandidatePoi]:
    """Construct an open route. The first point is nearest the arrival/access point."""
    unvisited = list(items)
    if len(unvisited) <= 1:
        return unvisited

    if start is not None:
        current = min(unvisited, key=lambda item: haversine_km(start, item.location))
    else:
        # A deterministic edge of the cluster makes the path traverse rather than loop.
        current = min(unvisited, key=lambda item: (item.location.lng, item.location.lat, item.id))
    ordered = [current]
    unvisited.remove(current)

    while unvisited:
        next_item = min(
            unvisited,
            key=lambda item: (matrix_metric(current, item, matrix, mode).duration_minutes, item.id),
        )
        ordered.append(next_item)
        unvisited.remove(next_item)
        current = next_item
    return ordered


def _untangle(route: list[CandidatePoi]) -> list[CandidatePoi]:
    """2-opt swap every geometric crossing, regardless of remote-matrix noise."""
    changed = True
    while changed:
        changed = False
        for i in range(len(route) - 1):
            for j in range(i + 2, len(route) - 1):
                if segments_intersect(route[i].location, route[i + 1].location, route[j].location, route[j + 1].location):
                    # Retain route[0] as the access-side start; reverse the middle segment.
                    route = route[: i + 1] + list(reversed(route[i + 1 : j + 1])) + route[j + 1 :]
                    changed = True
                    break
            if changed:
                break
    return route


def two_opt(
    initial_route: Sequence[CandidatePoi], *,
    matrix: Mapping[tuple[str, str], TravelMetric] | None = None,
    mode: str = 'driving', max_passes: int = 30,
) -> list[CandidatePoi]:
    """Open-path 2-opt: minimize movement while preserving the first access point."""
    route = _untangle(list(initial_route))
    if len(route) < 4:
        return route

    for _ in range(max_passes):
        improved = False
        for i in range(len(route) - 2):
            for j in range(i + 2, len(route)):
                candidate = route[: i + 1] + list(reversed(route[i + 1 : j + 1])) + route[j + 1 :]
                current_distance = path_distance(route, matrix, mode)
                candidate_distance = path_distance(candidate, matrix, mode)
                if candidate_distance + 1e-7 < current_distance:
                    route = candidate
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return _untangle(route)


def _centroid(items: Sequence[CandidatePoi]) -> tuple[float, float]:
    return (
        sum(item.location.lng for item in items) / len(items),
        sum(item.location.lat for item in items) / len(items),
    )


def _squared_distance_to_center(item: CandidatePoi, center: tuple[float, float]) -> float:
    # Longitude gets a modest latitude correction; sufficient at city scale.
    longitude_scale = cos(radians(item.location.lat))
    return ((item.location.lng - center[0]) * longitude_scale) ** 2 + (item.location.lat - center[1]) ** 2


def geographic_clusters(items: Sequence[CandidatePoi], days: int, max_iterations: int = 40) -> list[list[CandidatePoi]]:
    """Small deterministic K-Means implementation (no sklearn runtime dependency)."""
    points = list(items)
    if not points:
        return []
    k = max(1, min(days, len(points)))
    if k == 1:
        return [points]

    ordered = sorted(points, key=lambda item: (item.location.lng, item.location.lat, item.id))
    centers: list[tuple[float, float]] = []
    for index in range(k):
        point_index = round(index * (len(ordered) - 1) / (k - 1))
        centers.append((ordered[point_index].location.lng, ordered[point_index].location.lat))

    groups: list[list[CandidatePoi]] = [[] for _ in range(k)]
    for _ in range(max_iterations):
        groups = [[] for _ in range(k)]
        for point in points:
            group_index = min(range(k), key=lambda idx: (_squared_distance_to_center(point, centers[idx]), idx))
            groups[group_index].append(point)

        # Repair an empty cluster with the currently most remote item from a dense cluster.
        for group_index, group in enumerate(groups):
            if group:
                continue
            donor_index = max(range(k), key=lambda idx: len(groups[idx]))
            donor = max(groups[donor_index], key=lambda item: _squared_distance_to_center(item, centers[donor_index]))
            groups[donor_index].remove(donor)
            groups[group_index].append(donor)

        updated = [_centroid(group) for group in groups]
        drift = max(abs(old[0] - new[0]) + abs(old[1] - new[1]) for old, new in zip(centers, updated))
        centers = updated
        if drift < 1e-8:
            break
    return groups


def ordered_clusters(
    clusters: Sequence[Sequence[CandidatePoi]], start: Location | None = None,
) -> list[list[CandidatePoi]]:
    """Visit nearby regional clusters on consecutive days rather than bouncing across town."""
    remaining = [list(cluster) for cluster in clusters if cluster]
    if not remaining:
        return []
    if start is None:
        first_index = min(range(len(remaining)), key=lambda idx: (_centroid(remaining[idx])[0], _centroid(remaining[idx])[1]))
    else:
        first_index = min(
            range(len(remaining)),
            key=lambda idx: haversine_km(start, Location(lng=_centroid(remaining[idx])[0], lat=_centroid(remaining[idx])[1])),
        )
    result = [remaining.pop(first_index)]

    while remaining:
        previous_center = _centroid(result[-1])
        next_index = min(
            range(len(remaining)),
            key=lambda idx: (previous_center[0] - _centroid(remaining[idx])[0]) ** 2 + (previous_center[1] - _centroid(remaining[idx])[1]) ** 2,
        )
        result.append(remaining.pop(next_index))
    return result


def parse_opening_hours(value: str) -> tuple[int, int] | None:
    if not value or '全天' in value or '24' in value:
        return (0, 24 * 60)
    normalized = value.replace('–', '-').replace('—', '-').replace('至', '-').replace(' ', '')
    if '-' not in normalized:
        return None
    try:
        begin, end = normalized.split('-', maxsplit=1)
        begin_hour, begin_minute = (int(part) for part in begin.split(':', maxsplit=1))
        end_hour, end_minute = (int(part) for part in end.split(':', maxsplit=1))
        return (begin_hour * 60 + begin_minute, end_hour * 60 + end_minute)
    except (ValueError, IndexError):
        return None


def opening_adjusted_arrival(
    poi: CandidatePoi, arrival_minute: int, *, visit_date: date,
) -> int | None:
    if visit_date.weekday() in poi.closed_weekdays:
        return None
    window = parse_opening_hours(poi.opening_hours)
    if window is None:
        return arrival_minute
    opens, closes = window
    arrival = max(arrival_minute, opens)
    if arrival + poi.visit_minutes > closes:
        return None
    return arrival


def format_clock(total_minutes: int) -> str:
    total_minutes = total_minutes % (24 * 60)
    return f'{total_minutes // 60:02d}:{total_minutes % 60:02d}'


def schedule_route(
    route: Sequence[CandidatePoi], *, day_start_minute: int, daily_minutes: int,
    visit_date: date, matrix: Mapping[tuple[str, str], TravelMetric] | None = None,
    mode: str = 'driving', buffer_minutes: int = BUFFER_MINUTES,
) -> ScheduleResult:
    """Apply operating hours, a 15-minute inter-stop buffer, and a modest meal break."""
    current = day_start_minute
    cutoff = day_start_minute + daily_minutes
    scheduled: list[ScheduledItem] = []
    skipped: list[CandidatePoi] = []
    total_travel = 0
    total_distance = 0.0
    total_buffers = 0
    meal_reserved = False
    notices: list[str] = []

    for poi in route:
        if len(scheduled) >= 6:
            skipped.append(poi)
            continue
        travel = TravelMetric(0, 0)
        proposed = current
        if scheduled:
            travel = matrix_metric(scheduled[-1].poi, poi, matrix, mode)
            proposed += travel.duration_minutes + buffer_minutes

        # Preserve a non-rushed lunch/rest period if the selected POIs do not include food.
        reserve_meal = not meal_reserved and 'food' not in poi.categories and 11 * 60 + 40 <= proposed <= 13 * 60
        if reserve_meal:
            proposed += 40

        adjusted_arrival = opening_adjusted_arrival(poi, proposed, visit_date=visit_date)
        if adjusted_arrival is None:
            skipped.append(poi)
            continue
        if adjusted_arrival > proposed:
            notices.append(f'{poi.name} {format_clock(adjusted_arrival)} 开门，已自动顺延。')
        leave = adjusted_arrival + poi.visit_minutes
        if leave > cutoff:
            # The route is sorted spatially, so dropping its tail avoids a hidden cross-town fill.
            skipped.append(poi)
            continue
        if scheduled:
            total_travel += travel.duration_minutes
            total_distance += travel.distance_km
            total_buffers += buffer_minutes
        if reserve_meal:
            total_buffers += 40
            meal_reserved = True
            notices.append('已在午间预留 40 分钟用餐与休息时间。')
        scheduled.append(ScheduledItem(poi=poi, arrival_minute=adjusted_arrival, leave_minute=leave))
        current = leave

    if not scheduled:
        notices.append('所选时段内没有符合营业时间的景点，请调整出发时间或每日游玩时长。')
    return ScheduleResult(
        items=scheduled,
        skipped=skipped,
        total_travel_minutes=total_travel,
        total_distance_km=round(total_distance, 2),
        total_visit_minutes=sum(item.poi.visit_minutes for item in scheduled),
        total_buffer_minutes=total_buffers,
        notices=notices,
    )


def days_and_daily_minutes(duration_value: float, duration_unit: str, daily_hours: float) -> tuple[int, list[int]]:
    """Turn either a day count or a total-hour request into per-day hard budgets."""
    daily_minutes = round(daily_hours * 60)
    if duration_unit == 'days':
        days = max(1, round(duration_value))
        return days, [daily_minutes] * days
    total_minutes = round(duration_value * 60)
    days = max(1, (total_minutes + daily_minutes - 1) // daily_minutes)
    budgets = [daily_minutes] * days
    budgets[-1] = total_minutes - daily_minutes * (days - 1) or daily_minutes
    return days, budgets


def default_day_start(start_date: datetime | None, day_index: int) -> tuple[date, int]:
    if start_date is None:
        return date.today() + timedelta(days=day_index), 9 * 60
    target = (start_date + timedelta(days=day_index)).date()
    if day_index == 0:
        return target, start_date.hour * 60 + start_date.minute
    return target, 9 * 60
