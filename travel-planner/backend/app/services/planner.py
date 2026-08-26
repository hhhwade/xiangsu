"""Application service that turns a travel request into the public route JSON."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from math import ceil
from typing import Iterable

from app.config import Settings
from app.models import DayRoute, OverallStats, PlanResponse, RouteSpot, TravelRequest
from app.services.amap import AmapClient
from app.services.catalog import CandidatePoi, catalog_for_destination, rank_candidates
from app.services.optimizer import (
    ScheduleResult,
    TravelMetric,
    days_and_daily_minutes,
    default_day_start,
    estimated_metric,
    format_clock,
    geographic_clusters,
    matrix_metric,
    nearest_neighbor,
    ordered_clusters,
    route_has_crossings,
    schedule_route,
    two_opt,
)

COLORS = ('#DE7444', '#5E9C93', '#7A71B8', '#C58C45', '#4B86A4', '#A66573')
MODE_LABELS = {'walking': '步行', 'riding': '骑行', 'driving': '驾车', 'transit': '公共交通'}
TYPE_LABELS = {
    'natural': '自然风光', 'culture': '历史人文', 'food': '美食探店', 'family': '亲子乐园',
    'shopping': '购物商圈', 'trending': '网红打卡', 'museum': '博物馆', 'themePark': '主题乐园',
    'outdoor': '户外运动', 'temple': '宗教寺庙',
}
HANGZHOU_TITLES = ('西湖经典环线', '灵隐禅意与茶香', '运河人文慢游', '湖滨烟火漫游', '龙井茶山轻徒步', '钱塘江畔夜游')


def _mode_value(value: object) -> str:
    return str(getattr(value, 'value', value))


def _hours(minutes: int) -> str:
    return f'{minutes / 60:.1f}h'


def _kilometers(distance: float) -> str:
    return f'{distance:.1f}km'


def _title(destination: str, day: int, items: Iterable[CandidatePoi]) -> str:
    if '杭州' in destination and day <= len(HANGZHOU_TITLES):
        return HANGZHOU_TITLES[day - 1]
    categories = Counter(category for item in items for category in item.categories)
    primary = categories.most_common(1)[0][0] if categories else 'trending'
    suffix = {
        'natural': '山水慢游线', 'culture': '人文经典线', 'food': '风味探索线',
        'museum': '艺文漫游线', 'temple': '禅意静心线', 'shopping': '城市逛街线',
        'outdoor': '户外呼吸线', 'themePark': '欢乐畅玩线', 'family': '亲子轻松线',
        'trending': '城市灵感线',
    }.get(primary, '城市精选线')
    return f'{destination}{suffix}'


def _summary(items: list[CandidatePoi], distance: float) -> str:
    if not items:
        return '当前时段暂无可安排景点，建议调整出发时间。'
    types = '、'.join(dict.fromkeys(item.type for item in items[:3]))
    return f'将{types}集中在同一片区域，预计串联 {distance:.1f} km，减少跨区折返。'


class PlanningService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.amap = AmapClient(settings)

    async def _candidate_pool(self, request: TravelRequest, desired_count: int) -> tuple[list[CandidatePoi], str, list[str]]:
        preferences = [_mode_value(value) for value in request.preferences]
        warnings: list[str] = []
        from_amap = await self.amap.search_pois(request.destination, preferences, desired_count) if self.amap.enabled else []
        source = 'amap' if from_amap else 'fallback'
        candidates = from_amap or list(catalog_for_destination(request.destination))
        if not from_amap:
            warnings.append('当前使用本地演示景点池。部署后配置 AMAP_WEB_SERVICE_KEY 即可获取实时 POI、路况与营业信息。')

        ranked = rank_candidates(
            candidates,
            preferences,
            budget_max=request.budget.max if request.budget else None,
            needs_accessible=bool(request.group_size and request.group_size.accessible),
            special_needs=request.special_needs,
        )
        if len(ranked) < desired_count:
            warnings.append(f'符合条件的候选景点仅 {len(ranked)} 个，已优先保证路线集中度。')
        return ranked[:desired_count], source, warnings

    async def plan(self, request: TravelRequest) -> PlanResponse:
        days, day_budgets = days_and_daily_minutes(request.duration.value, request.duration.unit, request.daily_hours)
        desired_count = min(self.settings.max_candidate_pool, max(12, days * 6))
        candidates, source, warnings = await self._candidate_pool(request, desired_count)
        if not candidates:
            return PlanResponse(
                destination=request.destination,
                total_days=days,
                routes=[],
                overall_stats=OverallStats(total_distance='0.0km', total_spots=0, backtrack_check='warning', total_duration='0.0h'),
                generated_at=datetime.now(timezone.utc),
                source=source, warnings=[*warnings, '没有找到可用 POI，请尝试扩大区域或放宽偏好。'],
            )

        mode = _mode_value(request.transport_mode)
        matrix = await self.amap.travel_matrix(candidates, mode) if self.amap.enabled else {}
        if self.amap.enabled and not matrix:
            warnings.append('距离矩阵暂不可用，已用道路距离估算完成优化。')
            source = 'mixed' if source == 'amap' else source

        clusters = ordered_clusters(geographic_clusters(candidates, days), request.start_location)
        routes: list[DayRoute] = []
        total_distance = 0.0
        total_spots = 0
        any_crossing = False

        for index, cluster in enumerate(clusters):
            if index >= days:
                break
            # Dense clusters may contain more than one day's comfortable maximum. Keep the
            # highest-quality six, then make an open, geographic route through them.
            selected = sorted(cluster, key=lambda item: (-item.score, item.id))[:6]
            day_start_location = request.start_location if index == 0 else None
            initial = nearest_neighbor(selected, start=day_start_location, matrix=matrix, mode=mode)
            optimized = two_opt(initial, matrix=matrix, mode=mode)
            visit_date, start_minute = default_day_start(request.start_date, index)
            scheduled = schedule_route(
                optimized,
                day_start_minute=start_minute,
                daily_minutes=day_budgets[index],
                visit_date=visit_date,
                matrix=matrix,
                mode=mode,
            )

            # Removing a closed POI can create a new shortcut edge. Run the geometric
            # invariant again so the public path can never retain a crossing.
            if route_has_crossings([item.poi for item in scheduled.items]):
                repaired = two_opt([item.poi for item in scheduled.items], matrix=matrix, mode=mode)
                scheduled = schedule_route(
                    repaired, day_start_minute=start_minute, daily_minutes=day_budgets[index],
                    visit_date=visit_date, matrix=matrix, mode=mode,
                )

            # If an early opening-hours filter leaves a tiny day, attempt another nearby
            # POI in the same cluster before exposing a sparse itinerary.
            if len(scheduled.items) < 3:
                scheduled = self._try_fill_sparse_day(
                    scheduled, cluster, optimized, start_minute, day_budgets[index], visit_date, matrix, mode,
                )

            if route_has_crossings([item.poi for item in scheduled.items]):
                repaired = two_opt([item.poi for item in scheduled.items], matrix=matrix, mode=mode)
                scheduled = schedule_route(
                    repaired, day_start_minute=start_minute, daily_minutes=day_budgets[index],
                    visit_date=visit_date, matrix=matrix, mode=mode,
                )

            if len(scheduled.items) < 3:
                warnings.append(f'Day {index + 1} 可安排景点不足 3 个，建议延长每日可用时长或放宽偏好。')
            route = self._build_day_route(request.destination, index + 1, scheduled, matrix, mode)
            routes.append(route)
            total_distance += scheduled.total_distance_km
            total_spots += len(scheduled.items)
            if route_has_crossings([item.poi for item in scheduled.items]):
                any_crossing = True

        # K can be larger than the POI count. Preserve an explicit empty-day response rather
        # than silently pretending the requested time was fulfilled.
        for index in range(len(routes), days):
            routes.append(DayRoute(
                day=index + 1,
                title=f'{request.destination}自由探索日',
                color=COLORS[index % len(COLORS)], spots=[], total_distance='0.0km',
                total_visit_duration='0.0h', total_transport_duration='0.0h',
                summary='候选景点不足，建议扩大搜索范围或减少停留天数。',
                notices=['没有足够的同区域候选景点，未安排跨区折返路线。'],
            ))

        return PlanResponse(
            destination=request.destination,
            total_days=days,
            routes=routes,
            overall_stats=OverallStats(
                total_distance=_kilometers(total_distance),
                total_spots=total_spots,
                backtrack_check='warning' if any_crossing else 'passed',
                total_duration=_hours(sum(day_budgets)),
            ),
            generated_at=datetime.now(timezone.utc),
            source=source, warnings=warnings,
        )

    def _try_fill_sparse_day(
        self, existing: ScheduleResult, cluster: list[CandidatePoi], ordered: list[CandidatePoi], start_minute: int,
        daily_minutes: int, visit_date, matrix: dict[tuple[str, str], TravelMetric], mode: str,
    ) -> ScheduleResult:
        seen = {item.poi.id for item in existing.items}
        # Work only within the geographic cluster: no desperation trip across the city.
        additions = [item for item in cluster if item.id not in seen]
        candidate_route = [item.poi for item in existing.items]
        candidate_route.extend(additions)
        candidate_route = nearest_neighbor(candidate_route, matrix=matrix, mode=mode)
        candidate_route = two_opt(candidate_route, matrix=matrix, mode=mode)
        result = schedule_route(
            candidate_route, day_start_minute=start_minute, daily_minutes=daily_minutes,
            visit_date=visit_date, matrix=matrix, mode=mode,
        )
        return result if len(result.items) > len(existing.items) else existing

    def _build_day_route(
        self, destination: str, day: int, scheduled: ScheduleResult,
        matrix: dict[tuple[str, str], TravelMetric], mode: str,
    ) -> DayRoute:
        spots: list[RouteSpot] = []
        for index, item in enumerate(scheduled.items):
            next_item = scheduled.items[index + 1] if index + 1 < len(scheduled.items) else None
            next_metric = matrix_metric(item.poi, next_item.poi, matrix, mode) if next_item else None
            type_name = item.poi.type or TYPE_LABELS.get(item.poi.categories[0], '景点')
            spots.append(RouteSpot(
                id=item.poi.id,
                name=item.poi.name,
                type=type_name,
                location=item.poi.location,
                estimated_duration=item.poi.visit_minutes,
                priority=index + 1,
                arrival_time=format_clock(item.arrival_minute),
                leave_time=format_clock(item.leave_minute),
                next_spot=next_item.poi.name if next_item else None,
                next_distance=_kilometers(next_metric.distance_km) if next_metric else None,
                next_duration=f'{MODE_LABELS.get(mode, "驾车")} {next_metric.duration_minutes}分钟' if next_metric else None,
                tips=item.poi.tips,
                open_hours=item.poi.opening_hours,
            ))
        notices = [
            '同一区域景点已聚类安排；路线按最近邻 + 2-opt 完成无交叉优化。',
            '每两处景点间已预留 15 分钟弹性缓冲。',
            *scheduled.notices[:3],
        ]
        if scheduled.skipped:
            notices.append(f'已跳过 {len(scheduled.skipped)} 个不符合当前时段或总时长的候选景点。')
        return DayRoute(
            day=day,
            title=_title(destination, day, [item.poi for item in scheduled.items]),
            color=COLORS[(day - 1) % len(COLORS)],
            spots=spots,
            total_distance=_kilometers(scheduled.total_distance_km),
            total_visit_duration=_hours(scheduled.total_visit_minutes),
            total_transport_duration=_hours(scheduled.total_travel_minutes),
            summary=_summary([item.poi for item in scheduled.items], scheduled.total_distance_km),
            notices=notices,
        )

    async def reorder(self, request: TravelRequest, day: int, ordered_spot_ids: list[str]) -> PlanResponse:
        """Replan from the latest request and honor only valid IDs supplied by drag/drop."""
        plan = await self.plan(request)
        target = next((route for route in plan.routes if route.day == day), None)
        if target is None:
            return plan
        by_id = {spot.id: spot for spot in target.spots}
        order = [spot_id for spot_id in ordered_spot_ids if spot_id in by_id]
        if len(order) != len(target.spots):
            # Missing IDs are appended so a malformed client request never loses a POI.
            order.extend(spot.id for spot in target.spots if spot.id not in order)
        target.spots = [by_id[spot_id] for spot_id in order]
        for index, spot in enumerate(target.spots):
            spot.priority = index + 1
            spot.next_spot = target.spots[index + 1].name if index + 1 < len(target.spots) else None
        target.notices = ['已按拖拽顺序重排；生产环境可在此触发完整时间矩阵重算。', *target.notices]
        return plan
