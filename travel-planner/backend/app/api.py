from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.models import DestinationSuggestion, PlanResponse, ReorderRequest, TravelRequest
from app.services.catalog import CITY_POOLS
from app.services.planner import PlanningService

router = APIRouter(prefix='/api/v1', tags=['planner'])


@lru_cache
def _service() -> PlanningService:
    return PlanningService(get_settings())


def get_planning_service() -> PlanningService:
    return _service()


@router.get('/health', tags=['system'])
async def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    return {
        'status': 'ok',
        'service': 'travel-route-planner',
        'amapWebServiceConfigured': bool(settings.amap_web_service_key),
        'optimizer': 'geographic-kmeans + nearest-neighbor + 2-opt',
    }


@router.get('/destinations/autocomplete', response_model=list[DestinationSuggestion])
async def autocomplete(
    q: str = Query(min_length=1, max_length=80),
    service: PlanningService = Depends(get_planning_service),
) -> list[DestinationSuggestion]:
    remote = await service.amap.autocomplete(q)
    if remote:
        return remote
    # Deterministic offline suggestions make the form usable before a key is installed.
    needle = q.strip().replace('市', '')
    return [DestinationSuggestion(name=name) for name in CITY_POOLS if needle in name][:8]


@router.post('/plans', response_model=PlanResponse, response_model_by_alias=True)
async def create_plan(
    request: TravelRequest,
    service: PlanningService = Depends(get_planning_service),
) -> PlanResponse:
    return await service.plan(request)


@router.post('/plans/reorder', response_model=PlanResponse, response_model_by_alias=True)
async def reorder_plan(
    payload: ReorderRequest,
    service: PlanningService = Depends(get_planning_service),
) -> PlanResponse:
    return await service.reorder(payload.request, payload.day, payload.ordered_spot_ids)
