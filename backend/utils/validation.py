"""Input validation helpers for backend routes and services."""

from __future__ import annotations

from typing import Any, Mapping

from .helpers import clamp_score, clean_string, parse_tags

ALLOWED_THEMES = {"balanced", "nature", "historic", "waterfront", "city", "custom"}


class ValidationError(ValueError):
    """Raised when request input is missing or invalid."""

    def __init__(self, message: str, errors: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

    def to_dict(self) -> dict[str, Any]:
        return {"message": self.message, "errors": self.errors}


def _first_present(payload: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _required_text(value: Any, field_name: str, errors: dict[str, str]) -> str:
    text = clean_string(value)
    if not text:
        errors[field_name] = "This field is required."
    return text


def _optional_positive_float(
    value: Any,
    field_name: str,
    errors: dict[str, str],
) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors[field_name] = "Must be a number."
        return None
    if number <= 0:
        errors[field_name] = "Must be greater than 0."
        return None
    return number


def _required_positive_float(
    value: Any,
    field_name: str,
    errors: dict[str, str],
) -> float | None:
    if value in (None, ""):
        errors[field_name] = "This field is required."
        return None
    return _optional_positive_float(value, field_name, errors)


def _optional_score(value: Any, field_name: str, errors: dict[str, str]) -> int:
    if value in (None, ""):
        return 50
    try:
        return clamp_score(value)
    except (TypeError, ValueError):
        errors[field_name] = "Must be a number from 0 to 100."
        return 50


def _optional_ratio(value: Any, field_name: str, errors: dict[str, str]) -> float:
    if value in (None, ""):
        return 0.6
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors[field_name] = "Must be a number from 0 to 1."
        return 0.6
    if not 0 <= number <= 1:
        errors[field_name] = "Must be between 0 and 1."
        return 0.6
    return number


def _optional_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def validate_route_request(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate a route generation request from the React frontend."""
    if not isinstance(payload, Mapping):
        raise ValidationError("Invalid request body.", {"body": "Expected a JSON object."})

    errors: dict[str, str] = {}
    start_location = _required_text(
        _first_present(payload, "start_location", "start", "origin"),
        "start_location",
        errors,
    )
    end_location = _required_text(
        _first_present(payload, "end_location", "end", "destination"),
        "end_location",
        errors,
    )

    theme = clean_string(payload.get("theme", "balanced")).lower() or "balanced"
    if theme not in ALLOWED_THEMES:
        errors["theme"] = f"Must be one of: {', '.join(sorted(ALLOWED_THEMES))}."

    max_distance_km = _optional_positive_float(
        payload.get("max_distance_km"),
        "max_distance_km",
        errors,
    )
    scenic_priority = _optional_ratio(
        payload.get("scenic_priority"),
        "scenic_priority",
        errors,
    )

    if start_location and end_location and start_location.lower() == end_location.lower():
        errors["end_location"] = "Destination must be different from the start location."

    if errors:
        raise ValidationError("Route request validation failed.", errors)

    return {
        "start_location": start_location,
        "end_location": end_location,
        "theme": theme,
        "max_distance_km": max_distance_km,
        "scenic_priority": scenic_priority,
        "avoid_highways": _optional_bool(payload.get("avoid_highways", False)),
        "preferred_tags": parse_tags(payload.get("preferred_tags")),
    }


def validate_landmark_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate data before inserting or updating a landmark."""
    if not isinstance(payload, Mapping):
        raise ValidationError("Invalid landmark body.", {"body": "Expected a JSON object."})

    errors: dict[str, str] = {}
    name = _required_text(payload.get("name"), "name", errors)
    category = clean_string(payload.get("category", "scenic")).lower() or "scenic"
    description = clean_string(payload.get("description", ""))

    latitude = _parse_coordinate(payload.get("latitude"), "latitude", -90, 90, errors)
    longitude = _parse_coordinate(payload.get("longitude"), "longitude", -180, 180, errors)
    scenic_score = _optional_score(payload.get("scenic_score", 50), "scenic_score", errors)

    if errors:
        raise ValidationError("Landmark validation failed.", errors)

    return {
        "name": name,
        "category": category,
        "latitude": latitude,
        "longitude": longitude,
        "description": description,
        "scenic_score": scenic_score,
    }


def validate_edge_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate a scenic road segment before storing it."""
    if not isinstance(payload, Mapping):
        raise ValidationError("Invalid edge body.", {"body": "Expected a JSON object."})

    errors: dict[str, str] = {}
    start_node = _required_text(payload.get("start_node"), "start_node", errors)
    end_node = _required_text(payload.get("end_node"), "end_node", errors)
    distance_km = _required_positive_float(payload.get("distance_km"), "distance_km", errors)
    travel_time_min = _required_positive_float(
        payload.get("travel_time_min"),
        "travel_time_min",
        errors,
    )
    scenic_score = _optional_score(payload.get("scenic_score", 50), "scenic_score", errors)

    if start_node and end_node and start_node.lower() == end_node.lower():
        errors["end_node"] = "End node must be different from start node."

    if errors:
        raise ValidationError("Scenic edge validation failed.", errors)

    return {
        "start_node": start_node,
        "end_node": end_node,
        "distance_km": distance_km,
        "travel_time_min": travel_time_min,
        "scenic_score": scenic_score,
        "road_name": clean_string(payload.get("road_name", "")),
        "tags": parse_tags(payload.get("tags")),
    }


def validate_route_id(route_id: Any) -> int:
    """Validate URL route ids before querying SQLite."""
    try:
        parsed_id = int(route_id)
    except (TypeError, ValueError):
        raise ValidationError("Invalid route id.", {"route_id": "Must be an integer."})
    if parsed_id <= 0:
        raise ValidationError("Invalid route id.", {"route_id": "Must be greater than 0."})
    return parsed_id


def _parse_coordinate(
    value: Any,
    field_name: str,
    minimum: float,
    maximum: float,
    errors: dict[str, str],
) -> float | None:
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        errors[field_name] = "Must be a valid coordinate."
        return None
    if not minimum <= coordinate <= maximum:
        errors[field_name] = f"Must be between {minimum} and {maximum}."
        return None
    return coordinate
