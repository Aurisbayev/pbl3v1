"""Flask endpoints for scenic route generation and route history."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.database import get_saved_route, list_landmarks, list_saved_routes
from backend.services import (
    MapProcessingError,
    NavigationProcessingError,
    build_map_payload,
    generate_navigation_route,
)
from utils.helpers import error_response, success_response
from utils.validation import ValidationError, validate_route_id


route_bp = Blueprint("route_routes", __name__, url_prefix="/api/routes")

ROUTE_THEMES = [
    {
        "id": "balanced",
        "label": "Balanced",
        "description": "Mixes scenic quality with travel time.",
    },
    {
        "id": "nature",
        "label": "Nature",
        "description": "Prioritizes parks, gardens, trails, and green spaces.",
    },
    {
        "id": "historic",
        "label": "Historic",
        "description": "Prioritizes temples, shrines, museums, and heritage spots.",
    },
    {
        "id": "waterfront",
        "label": "Waterfront",
        "description": "Prioritizes rivers, canals, bridges, lakes, and coastlines.",
    },
    {
        "id": "city",
        "label": "City",
        "description": "Prioritizes downtown views, stations, shopping, and architecture.",
    },
    {
        "id": "custom",
        "label": "Custom",
        "description": "Uses the tags selected by the user.",
    },
]


@route_bp.get("/options")
def get_route_options():
    """Return route-selection data used by the React form."""
    try:
        data = {
            "themes": ROUTE_THEMES,
            "landmarks": list_landmarks(),
        }
        return _json(success_response(data, "Route options loaded."))
    except Exception:
        return _json(
            error_response(
                "Could not load route options.",
                {"server": "Please try again later."},
                500,
            )
        )


@route_bp.post("/generate")
def generate_route():
    """Generate a scenic route from frontend preferences."""
    try:
        payload = _json_body()
        result = generate_navigation_route(payload)
        return _json(success_response(result, "Route generated successfully.", 201))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except NavigationProcessingError as error:
        return _json(error_response(error.message, error.errors, 422))
    except Exception:
        return _json(
            error_response(
                "Route generation failed.",
                {"server": "Please check the request and try again."},
                500,
            )
        )


@route_bp.get("/history")
def get_route_history():
    """Return recently generated routes saved in SQLite."""
    try:
        limit = _positive_int_query("limit", default=20, maximum=100)
        routes = list_saved_routes(limit=limit)
        data = {
            "items": routes,
            "total": len(routes),
            "limit": limit,
        }
        return _json(success_response(data, "Route history loaded."))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except Exception:
        return _json(
            error_response(
                "Could not load route history.",
                {"server": "Please try again later."},
                500,
            )
        )


@route_bp.get("/<route_id>")
def get_route(route_id: str):
    """Return one saved route by id."""
    try:
        saved_route_id = validate_route_id(route_id)
        saved_route = get_saved_route(saved_route_id)
        if saved_route is None:
            return _json(
                error_response(
                    "Route was not found.",
                    {"route_id": "No saved route exists for this id."},
                    404,
                )
            )
        return _json(success_response(saved_route, "Route loaded."))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except Exception:
        return _json(
            error_response(
                "Could not load the route.",
                {"server": "Please try again later."},
                500,
            )
        )


@route_bp.get("/<route_id>/map")
def get_route_map(route_id: str):
    """Return map coordinates, markers, bounds, and GeoJSON for a saved route."""
    try:
        saved_route_id = validate_route_id(route_id)
        saved_route = get_saved_route(saved_route_id)
        if saved_route is None:
            return _json(
                error_response(
                    "Route was not found.",
                    {"route_id": "No saved route exists for this id."},
                    404,
                )
            )

        map_payload = build_map_payload(saved_route["route"])
        return _json(success_response(map_payload, "Route map loaded."))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except MapProcessingError as error:
        return _json(error_response(error.message, error.errors, 422))
    except Exception:
        return _json(
            error_response(
                "Could not build the route map.",
                {"server": "Please try again later."},
                500,
            )
        )


def _json_body() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError(
            "Invalid request body.",
            {"body": "Expected a JSON object."},
        )
    return payload


def _positive_int_query(
    name: str,
    *,
    default: int,
    maximum: int,
) -> int:
    raw_value = request.args.get(name, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ValidationError(
            "Invalid query parameter.",
            {name: "Must be an integer."},
        )

    if value < 1:
        raise ValidationError(
            "Invalid query parameter.",
            {name: "Must be greater than 0."},
        )
    if value > maximum:
        raise ValidationError(
            "Invalid query parameter.",
            {name: f"Must be {maximum} or less."},
        )
    return value


def _json(response: tuple[dict[str, Any], int]):
    payload, status_code = response
    return jsonify(payload), status_code
