"""Common helper functions shared across backend routes and services."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any, Iterable, Sequence


def now_iso() -> str:
    """Return the current time in a frontend-friendly ISO format."""
    return datetime.now(UTC).isoformat()


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside an inclusive range."""
    return max(minimum, min(maximum, value))


def clamp_score(score: float) -> int:
    """Normalize a scenic score to an integer between 0 and 100."""
    return int(round(clamp(float(score), 0, 100)))


def clean_string(value: Any) -> str:
    """Trim user-provided text and collapse repeated whitespace."""
    return " ".join(str(value).strip().split())


def parse_tags(value: Any) -> list[str]:
    """Normalize tags from comma-separated strings or iterables."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_tags = value.split(",")
    elif isinstance(value, Iterable):
        raw_tags = value
    else:
        raw_tags = [value]
    tags = []
    for tag in raw_tags:
        normalized = clean_string(tag).lower()
        if normalized and normalized not in tags:
            tags.append(normalized)
    return tags


def haversine_distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Calculate straight-line distance between two coordinates."""
    earth_radius_km = 6371.0088
    lat_a = math.radians(latitude_a)
    lon_a = math.radians(longitude_a)
    lat_b = math.radians(latitude_b)
    lon_b = math.radians(longitude_b)

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(earth_radius_km * c, 3)


def build_response(
    success: bool,
    data: Any = None,
    message: str | None = None,
    errors: Any = None,
) -> dict[str, Any]:
    """Create the consistent JSON shape returned by API endpoints."""
    response: dict[str, Any] = {
        "success": success,
        "timestamp": now_iso(),
    }
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
    if errors:
        response["errors"] = errors
    return response


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> tuple[dict[str, Any], int]:
    """Return a success payload and HTTP status code."""
    return build_response(True, data=data, message=message), status_code


def error_response(
    message: str,
    errors: Any = None,
    status_code: int = 400,
) -> tuple[dict[str, Any], int]:
    """Return an error payload and HTTP status code."""
    return build_response(False, message=message, errors=errors), status_code


def paginate(
    items: Sequence[Any],
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """Return one page of items with pagination metadata."""
    safe_page = max(1, int(page))
    safe_per_page = max(1, min(int(per_page), 100))
    start = (safe_page - 1) * safe_per_page
    end = start + safe_per_page
    total = len(items)
    return {
        "items": list(items[start:end]),
        "page": safe_page,
        "per_page": safe_per_page,
        "total": total,
        "total_pages": math.ceil(total / safe_per_page) if total else 0,
    }


def round_route_number(value: float) -> float:
    """Round route distances or times without hiding useful decimals."""
    return round(float(value), 2)
