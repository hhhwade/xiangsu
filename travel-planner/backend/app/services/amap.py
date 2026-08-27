"""Server-side adapter for AMap Web Service APIs.

Only the server receives AMAP_WEB_SERVICE_KEY. Browser map rendering uses a separately
restricted JS key; neither key is committed or serialized in plan responses.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Iterable

import httpx

from app.config import Settings
from app.models import DestinationSuggestion, Location
from app.services.catalog import CandidatePoi
from app.services.optimizer import TravelMetric


PREFERENCE_KEYWORDS: dict[str, str] = {
    'natural': '风景名胜 公园 湖泊',
    'culture': '名胜古迹 历史文化',
    'food': '餐饮服务 特色美食',
    'family': '亲子乐园 动物园',
    'shopping': '购物中心 步行街',
    'trending': '网红打卡 景点',
    'museum': '博物馆 展览馆',
    'themePark': '主题乐园 游乐园',
    'outdoor': '登山 徒步 公园',
    'temple': '寺庙 道观',
}


@dataclass
class _CacheEntry:
    expires_at: float
    value: Any


class TtlMemoryCache:
    """Bounded local fallback; Redis can replace this adapter without API changes."""

    def __init__(self, max_entries: int = 512) -> None:
        self._values: dict[str, _CacheEntry] = {}
        self._max_entries = max_entries

    def get(self, key: str) -> Any | None:
        entry = self._values.get(key)
        if entry is None or entry.expires_at < time.monotonic():
            self._values.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if len(self._values) >= self._max_entries:
            oldest = min(self._values, key=lambda item: self._values[item].expires_at)
            self._values.pop(oldest, None)
        self._values[key] = _CacheEntry(time.monotonic() + ttl_seconds, value)


class AmapClient:
    base_url = 'https://restapi.amap.com'

    def __init__(self, settings: Settings, cache: TtlMemoryCache | None = None) -> None:
        self.settings = settings
        self.cache = cache or TtlMemoryCache()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.amap_web_service_key)

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        params = {**params, 'key': self.settings.amap_web_service_key}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(f'{self.base_url}{path}', params=params)
                response.raise_for_status()
                payload = response.json()
                if str(payload.get('status')) != '1':
                    return None
                return payload
        except (httpx.HTTPError, ValueError):
            return None

    async def geocode(self, address: str) -> Location | None:
        cache_key = f'geocode:{address}'
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        payload = await self._get('/v3/geocode/geo', {'address': address})
        try:
            location = payload['geocodes'][0]['location'] if payload else ''
            lng, lat = (float(value) for value in location.split(',', maxsplit=1))
            result = Location(lng=lng, lat=lat)
        except (KeyError, IndexError, ValueError, AttributeError):
            result = None
        self.cache.set(cache_key, result, self.settings.planning_cache_ttl_seconds)
        return result

    async def autocomplete(self, keyword: str) -> list[DestinationSuggestion]:
        keyword = keyword.strip()
        if not keyword:
            return []
        cache_key = f'autocomplete:{keyword}'
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        payload = await self._get('/v3/assistant/inputtips', {'keywords': keyword, 'citylimit': 'false'})
        result: list[DestinationSuggestion] = []
        for item in (payload or {}).get('tips', [])[:8]:
            if not item.get('name'):
                continue
            loc: Location | None = None
            try:
                lng, lat = (float(value) for value in item.get('location', '').split(',', maxsplit=1))
                loc = Location(lng=lng, lat=lat)
            except (ValueError, AttributeError):
                pass
            result.append(DestinationSuggestion(name=item['name'], district=item.get('district'), location=loc))
        self.cache.set(cache_key, result, 3600)
        return result

    def _categories_from_type(self, raw_type: str) -> tuple[str, ...]:
        text = raw_type or ''
        categories: list[str] = []
        matcher = {
            'natural': ('风景', '公园', '湖泊', '山'),
            'culture': ('古迹', '文化', '名胜', '故居'),
            'food': ('餐饮', '美食', '饭店'),
            'family': ('动物园', '亲子', '儿童'),
            'shopping': ('购物', '商场', '步行街'),
            'trending': ('景点', '休闲'),
            'museum': ('博物馆', '展览'),
            'themePark': ('游乐', '主题公园'),
            'outdoor': ('体育', '登山', '公园'),
            'temple': ('寺庙', '道观', '宗教'),
        }
        for name, snippets in matcher.items():
            if any(snippet in text for snippet in snippets):
                categories.append(name)
        return tuple(categories or ('trending',))

    @staticmethod
    def _duration_for_categories(categories: Iterable[str]) -> int:
        catalog = {
            'themePark': 300, 'outdoor': 180, 'museum': 130, 'culture': 100,
            'shopping': 110, 'natural': 85, 'food': 75, 'temple': 75,
            'family': 120, 'trending': 55,
        }
        return max((catalog.get(category, 75) for category in categories), default=75)

    async def search_pois(self, destination: str, preferences: Iterable[str], limit: int) -> list[CandidatePoi]:
        """Fetch and normalize AMap POIs. Errors intentionally return an empty list."""
        selected = list(preferences)[:5] or ['natural', 'culture', 'food']
        cache_key = f'pois:{destination}:{"|".join(sorted(selected))}:{limit}'
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        async def search_one(preference: str) -> dict[str, Any] | None:
            return await self._get('/v3/place/text', {
                'keywords': PREFERENCE_KEYWORDS.get(preference, preference),
                'city': destination,
                'citylimit': 'true',
                'offset': min(25, max(10, limit)),
                'page': 1,
                'extensions': 'all',
            })

        payloads = await asyncio.gather(*(search_one(preference) for preference in selected))
        seen: set[str] = set()
        result: list[CandidatePoi] = []
        for payload in payloads:
            for item in (payload or {}).get('pois', []):
                poi_id = item.get('id')
                if not poi_id or poi_id in seen or not item.get('name'):
                    continue
                try:
                    lng, lat = (float(value) for value in item.get('location', '').split(',', maxsplit=1))
                except (ValueError, AttributeError):
                    continue
                seen.add(poi_id)
                categories = self._categories_from_type(item.get('type', ''))
                detail = item.get('biz_ext') or {}
                rating = detail.get('rating')
                try:
                    score = float(rating) if rating else 4.2
                except (TypeError, ValueError):
                    score = 4.2
                result.append(CandidatePoi(
                    id=poi_id,
                    name=item['name'],
                    type=(item.get('type') or '景点').split(';')[0],
                    categories=categories,
                    location=Location(lng=lng, lat=lat),
                    visit_minutes=self._duration_for_categories(categories),
                    opening_hours=detail.get('opentime') or '以现场公示为准',
                    tips=item.get('address') or '请在出发前确认预约与开放安排。',
                    score=score,
                ))
                if len(result) >= limit:
                    break
            if len(result) >= limit:
                break
        self.cache.set(cache_key, result, self.settings.planning_cache_ttl_seconds)
        return result

    async def travel_matrix(self, points: list[CandidatePoi], mode: str) -> dict[tuple[str, str], TravelMetric]:
        """Use AMap distance matrix when available; the optimizer fills missing legs.

        AMap's v3 distance endpoint accepts multiple origins per destination. We call
        once per destination instead of N² individual routing requests, and gracefully
        leave malformed or rate-limited legs for geometric fallback.
        """
        if not self.enabled or len(points) < 2:
            return {}
        cache_key = f'matrix:{mode}:{"|".join(point.id for point in points)}'
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        type_by_mode = {'driving': 1, 'walking': 3, 'riding': 3, 'transit': 1}
        origins = '|'.join(f'{point.location.lng},{point.location.lat}' for point in points)

        async def one_destination(destination: CandidatePoi) -> tuple[CandidatePoi, dict[str, Any] | None]:
            response = await self._get('/v3/distance', {
                'origins': origins,
                'destination': f'{destination.location.lng},{destination.location.lat}',
                'type': type_by_mode.get(mode, 1),
            })
            return destination, response

        payloads = await asyncio.gather(*(one_destination(point) for point in points))
        matrix: dict[tuple[str, str], TravelMetric] = {}
        for destination, payload in payloads:
            results = (payload or {}).get('results', [])
            for origin, item in zip(points, results):
                if origin.id == destination.id:
                    continue
                try:
                    distance = float(item['distance']) / 1000
                    duration = max(1, round(float(item['duration']) / 60))
                except (KeyError, TypeError, ValueError):
                    continue
                matrix[(origin.id, destination.id)] = TravelMetric(round(distance, 2), duration, source='amap')
        self.cache.set(cache_key, matrix, min(300, self.settings.planning_cache_ttl_seconds))
        return matrix
