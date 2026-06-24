"""Lightweight database models used by the SQLite layer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


def _row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    return dict(row)


def _parse_json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list, tuple)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _parse_tags(value: Any) -> tuple[str, ...]:
    tags = _parse_json(value, [])
    if isinstance(tags, str):
        return (tags,)
    return tuple(str(tag).strip().lower() for tag in tags if str(tag).strip())


@dataclass(frozen=True)
class Landmark:
    """A point of interest that can increase a route's scenic value."""

    name: str
    category: str
    latitude: float
    longitude: float
    description: str = ""
    scenic_score: int = 50
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> "Landmark":
        data = _row_to_dict(row)
        return cls(
            id=data.get("id"),
            name=data["name"],
            category=data.get("category", "scenic"),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            description=data.get("description") or "",
            scenic_score=int(data.get("scenic_score", 50)),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_record(self) -> tuple[Any, ...]:
        return (
            self.name,
            self.category,
            self.latitude,
            self.longitude,
            self.description,
            self.scenic_score,
        )


@dataclass(frozen=True)
class ScenicEdge:
    """A road or path segment between two route nodes."""

    start_node: str
    end_node: str
    distance_km: float
    travel_time_min: float
    scenic_score: int
    road_name: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> "ScenicEdge":
        data = _row_to_dict(row)
        return cls(
            id=data.get("id"),
            start_node=data["start_node"],
            end_node=data["end_node"],
            distance_km=float(data["distance_km"]),
            travel_time_min=float(data["travel_time_min"]),
            scenic_score=int(data["scenic_score"]),
            road_name=data.get("road_name") or "",
            tags=_parse_tags(data.get("tags")),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    def to_record(self) -> tuple[Any, ...]:
        return (
            self.start_node,
            self.end_node,
            self.distance_km,
            self.travel_time_min,
            self.scenic_score,
            self.road_name,
            json.dumps(list(self.tags)),
        )


@dataclass(frozen=True)
class SavedRoute:
    """A generated route saved for history, review, or later navigation."""

    start_location: str
    end_location: str
    theme: str
    route: dict[str, Any]
    scenic_score: float
    distance_km: float
    estimated_time_min: float
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> "SavedRoute":
        data = _row_to_dict(row)
        return cls(
            id=data.get("id"),
            start_location=data["start_location"],
            end_location=data["end_location"],
            theme=data.get("theme", "balanced"),
            route=_parse_json(data.get("route_json"), {}),
            scenic_score=float(data.get("scenic_score", 0)),
            distance_km=float(data.get("distance_km", 0)),
            estimated_time_min=float(data.get("estimated_time_min", 0)),
            created_at=data.get("created_at"),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SavedRoute":
        route = data.get("route") or data.get("route_json") or {}
        if isinstance(route, str):
            route = _parse_json(route, {})
        return cls(
            id=data.get("id"),
            start_location=str(data["start_location"]),
            end_location=str(data["end_location"]),
            theme=str(data.get("theme", "balanced")),
            route=dict(route),
            scenic_score=float(data.get("scenic_score", 0)),
            distance_km=float(data.get("distance_km", 0)),
            estimated_time_min=float(data.get("estimated_time_min", 0)),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_record(self) -> tuple[Any, ...]:
        return (
            self.start_location,
            self.end_location,
            self.theme,
            json.dumps(self.route),
            self.scenic_score,
            self.distance_km,
            self.estimated_time_min,
        )
