from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def to_camel(value: str) -> str:
    head, *tail = value.split('_')
    return head + ''.join(part.capitalize() for part in tail)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, use_enum_values=True)


class TransportMode(str, Enum):
    walking = 'walking'
    riding = 'riding'
    driving = 'driving'
    transit = 'transit'


class Preference(str, Enum):
    natural = 'natural'
    culture = 'culture'
    food = 'food'
    family = 'family'
    shopping = 'shopping'
    trending = 'trending'
    museum = 'museum'
    theme_park = 'themePark'
    outdoor = 'outdoor'
    temple = 'temple'


class Duration(CamelModel):
    value: float = Field(ge=1, le=720, description='天数或小时数')
    unit: Literal['days', 'hours']

    @field_validator('value')
    @classmethod
    def days_cannot_exceed_thirty(cls, value: float, info):
        # The corresponding unit is checked in the model-level validator.
        return value

    @model_validator(mode='after')
    def validate_duration(self):
        if self.unit == 'days' and self.value > 30:
            raise ValueError('duration.value must be between 1 and 30 when unit is days')
        return self


class Budget(CamelModel):
    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)

    @model_validator(mode='after')
    def validate_range(self):
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError('budget.min cannot exceed budget.max')
        return self


class GroupSize(CamelModel):
    adults: int = Field(default=1, ge=0, le=50)
    children: int = Field(default=0, ge=0, le=50)
    elderly: bool = False
    accessible: bool = False

    @model_validator(mode='after')
    def at_least_one_guest(self):
        if self.adults + self.children < 1:
            raise ValueError('at least one traveller is required')
        return self


class Location(CamelModel):
    lng: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)


class TravelRequest(CamelModel):
    destination: str = Field(min_length=1, max_length=120)
    duration: Duration
    preferences: list[Preference] = Field(default_factory=list, max_length=10)
    transport_mode: TransportMode = TransportMode.driving
    daily_hours: float = Field(default=8, ge=2, le=16)
    budget: Budget | None = None
    group_size: GroupSize | None = None
    start_date: datetime | None = None
    special_needs: str | None = Field(default=None, max_length=500)
    start_location: Location | None = None

    @field_validator('destination')
    @classmethod
    def clean_destination(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('destination cannot be empty')
        return value

    @field_validator('special_needs')
    @classmethod
    def clean_special_needs(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class RouteSpot(CamelModel):
    id: str
    name: str
    type: str
    location: Location
    estimated_duration: int
    priority: int
    arrival_time: str
    leave_time: str
    next_spot: str | None = None
    next_distance: str | None = None
    next_duration: str | None = None
    tips: str
    open_hours: str | None = None


class DayRoute(CamelModel):
    day: int
    title: str
    color: str
    spots: list[RouteSpot]
    total_distance: str
    total_visit_duration: str
    total_transport_duration: str
    summary: str
    notices: list[str] = Field(default_factory=list)


class OverallStats(CamelModel):
    total_distance: str
    total_spots: int
    backtrack_check: Literal['passed', 'warning']
    total_duration: str | None = None


class PlanResponse(CamelModel):
    destination: str
    total_days: int
    routes: list[DayRoute]
    overall_stats: OverallStats
    generated_at: datetime
    source: Literal['amap', 'fallback', 'mixed'] = 'fallback'
    warnings: list[str] = Field(default_factory=list)


class DestinationSuggestion(CamelModel):
    name: str
    district: str | None = None
    location: Location | None = None


class ReorderRequest(CamelModel):
    """Client-side drag result. The server validates and recomputes time labels."""

    request: TravelRequest
    day: int = Field(ge=1, le=30)
    ordered_spot_ids: list[str] = Field(min_length=1, max_length=12)
