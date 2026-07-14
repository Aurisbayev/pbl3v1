"""Flask endpoints for starting and updating route navigation."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from flask import Blueprint, jsonify, request

from database import get_saved_route
from services import MapProcessingError, build_map_payload
from utils.helpers import error_response, success_response
from utils.validation import ValidationError, validate_route_id


navigation_bp = Blueprint(
    "navigation_routes",
    __name__,
    url_prefix="/api/navigation",
)

ACTIVE_NAVIGATION_SESSIONS: dict[str, dict[str, Any]] = {}
ALLOWED_NAVIGATION_STATUSES = {"active", "paused", "completed", "cancelled"}


@navigation_bp.post("/start")
def start_navigation():
    """Start navigation using either a saved route id or a route object."""
    try:
        payload = _json_body()
        route = _route_from_payload(payload)
        map_payload = build_map_payload(route)
        steps = _navigation_steps(route)
        session_id = str(uuid4())
        session = {
            "session_id": session_id,
            "status": "active",
            "route": route,
            "summary": route.get("summary", {}),
            "map": map_payload,
            "steps": steps,
            "current_step_index": 0,
            "current_step": steps[0] if steps else None,
        }
        ACTIVE_NAVIGATION_SESSIONS[session_id] = session

        return _json(success_response(session, "Navigation started.", 201))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except MapProcessingError as error:
        return _json(error_response(error.message, error.errors, 422))
    except Exception:
        return _json(
            error_response(
                "Could not start navigation.",
                {"server": "Please check the route and try again."},
                500,
            )
        )


@navigation_bp.get("/<session_id>")
def get_navigation_session(session_id: str):
    """Return the current state of an active navigation session."""
    session = ACTIVE_NAVIGATION_SESSIONS.get(session_id)
    if session is None:
        return _json(
            error_response(
                "Navigation session was not found.",
                {"session_id": "Start navigation before requesting this session."},
                404,
            )
        )
    return _json(success_response(session, "Navigation session loaded."))


@navigation_bp.patch("/<session_id>")
def update_navigation_session(session_id: str):
    """Update navigation progress or status from the React navigation screen."""
    try:
        session = ACTIVE_NAVIGATION_SESSIONS.get(session_id)
        if session is None:
            return _json(
                error_response(
                    "Navigation session was not found.",
                    {"session_id": "Start navigation before updating this session."},
                    404,
                )
            )

        payload = _json_body()
        _apply_navigation_update(session, payload)
        return _json(success_response(session, "Navigation session updated."))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except Exception:
        return _json(
            error_response(
                "Could not update navigation.",
                {"server": "Please check the request and try again."},
                500,
            )
        )


@navigation_bp.delete("/<session_id>")
def stop_navigation(session_id: str):
    """End and remove a navigation session."""
    session = ACTIVE_NAVIGATION_SESSIONS.pop(session_id, None)
    if session is None:
        return _json(
            error_response(
                "Navigation session was not found.",
                {"session_id": "No active session exists for this id."},
                404,
            )
        )

    session["status"] = "cancelled"
    return _json(success_response(session, "Navigation stopped."))


def _route_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "route_id" in payload:
        route_id = validate_route_id(payload["route_id"])
        saved_route = get_saved_route(route_id)
        if saved_route is None:
            raise ValidationError(
                "Route was not found.",
                {"route_id": "No saved route exists for this id."},
            )
        return dict(saved_route["route"])

    route = payload.get("route")
    if isinstance(route, dict):
        return route

    generated_route = payload.get("generated_route")
    if isinstance(generated_route, dict) and isinstance(generated_route.get("route"), dict):
        return generated_route["route"]

    raise ValidationError(
        "Route is required.",
        {"route": "Send either route_id or a generated route object."},
    )


def _navigation_steps(route: dict[str, Any]) -> list[dict[str, Any]]:
    steps = []
    segments = route.get("segments", [])
    if not isinstance(segments, list):
        return steps

    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            continue
        start_node = segment.get("start_node", "current location")
        end_node = segment.get("end_node", "next point")
        road_name = segment.get("road_name") or "scenic route"
        steps.append(
            {
                "step_number": index,
                "instruction": f"Follow {road_name} from {start_node} to {end_node}.",
                "start_node": start_node,
                "end_node": end_node,
                "road_name": road_name,
                "distance_km": segment.get("distance_km", 0),
                "travel_time_min": segment.get("travel_time_min", 0),
                "scenic_score": segment.get("scenic_score", 0),
            }
        )
    return steps


def _apply_navigation_update(
    session: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    action = payload.get("action")
    steps = session.get("steps", [])

    if action == "next_step":
        session["current_step_index"] = min(
            session["current_step_index"] + 1,
            max(len(steps) - 1, 0),
        )
    elif action == "previous_step":
        session["current_step_index"] = max(session["current_step_index"] - 1, 0)
    elif action == "complete":
        session["status"] = "completed"
        session["current_step_index"] = max(len(steps) - 1, 0)
    elif action == "cancel":
        session["status"] = "cancelled"
    elif action not in (None, ""):
        raise ValidationError(
            "Invalid navigation action.",
            {"action": "Use next_step, previous_step, complete, or cancel."},
        )

    if "current_step_index" in payload:
        session["current_step_index"] = _validate_step_index(
            payload["current_step_index"],
            len(steps),
        )

    if "status" in payload:
        status = str(payload["status"]).strip().lower()
        if status not in ALLOWED_NAVIGATION_STATUSES:
            raise ValidationError(
                "Invalid navigation status.",
                {
                    "status": (
                        "Use active, paused, completed, or cancelled."
                    )
                },
            )
        session["status"] = status

    current_index = session["current_step_index"]
    session["current_step"] = steps[current_index] if steps else None


def _validate_step_index(value: Any, step_count: int) -> int:
    try:
        step_index = int(value)
    except (TypeError, ValueError):
        raise ValidationError(
            "Invalid current step.",
            {"current_step_index": "Must be an integer."},
        )

    if step_index < 0 or (step_count and step_index >= step_count):
        raise ValidationError(
            "Invalid current step.",
            {"current_step_index": "Step index is outside the route steps."},
        )
    if step_count == 0 and step_index != 0:
        raise ValidationError(
            "Invalid current step.",
            {"current_step_index": "Route has no navigation steps."},
        )
    return step_index


def _json_body() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError(
            "Invalid request body.",
            {"body": "Expected a JSON object."},
        )
    return payload


def _json(response: tuple[dict[str, Any], int]):
    payload, status_code = response
    return jsonify(payload), status_code
