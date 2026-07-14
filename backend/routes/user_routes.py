"""Flask endpoints for frontend user settings and route preferences."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from utils.helpers import clean_string, error_response, parse_tags, success_response
from utils.validation import ALLOWED_THEMES, ValidationError


user_bp = Blueprint("user_routes", __name__, url_prefix="/api/users")

DEFAULT_USER_PREFERENCES = {
    "theme": "balanced",
    "scenic_priority": 0.6,
    "avoid_highways": False,
    "preferred_tags": [],
    "default_start_location": "",
}


@user_bp.get("/me")
def get_current_user():
    """Return the current frontend user context."""
    data = {
        "user": {
            "id": "guest",
            "display_name": "Guest",
            "is_guest": True,
        },
        "preferences": DEFAULT_USER_PREFERENCES,
    }
    return _json(success_response(data, "User context loaded."))


@user_bp.get("/preferences")
def get_user_preferences():
    """Return default route preferences for the React form."""
    return _json(success_response(DEFAULT_USER_PREFERENCES, "User preferences loaded."))


@user_bp.post("/preferences")
@user_bp.patch("/preferences")
def save_user_preferences():
    """Validate route preferences sent by the React frontend."""
    try:
        payload = _json_body()
        preferences = _validate_preferences(payload)
        return _json(success_response(preferences, "User preferences saved."))
    except ValidationError as error:
        return _json(error_response(error.message, error.errors, 400))
    except Exception:
        return _json(
            error_response(
                "Could not save user preferences.",
                {"server": "Please check the request and try again."},
                500,
            )
        )


def _validate_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    errors: dict[str, str] = {}

    theme = clean_string(payload.get("theme", DEFAULT_USER_PREFERENCES["theme"])).lower()
    if not theme:
        theme = DEFAULT_USER_PREFERENCES["theme"]
    if theme not in ALLOWED_THEMES:
        errors["theme"] = f"Must be one of: {', '.join(sorted(ALLOWED_THEMES))}."

    scenic_priority = _optional_ratio(
        payload.get("scenic_priority", DEFAULT_USER_PREFERENCES["scenic_priority"]),
        "scenic_priority",
        errors,
    )
    avoid_highways = _optional_bool(
        payload.get("avoid_highways", DEFAULT_USER_PREFERENCES["avoid_highways"])
    )

    if errors:
        raise ValidationError("User preference validation failed.", errors)

    return {
        "theme": theme,
        "scenic_priority": scenic_priority,
        "avoid_highways": avoid_highways,
        "preferred_tags": parse_tags(payload.get("preferred_tags", [])),
        "default_start_location": clean_string(payload.get("default_start_location", "")),
    }


def _optional_ratio(value: Any, field_name: str, errors: dict[str, str]) -> float:
    if value in (None, ""):
        return DEFAULT_USER_PREFERENCES["scenic_priority"]
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors[field_name] = "Must be a number from 0 to 1."
        return DEFAULT_USER_PREFERENCES["scenic_priority"]
    if not 0 <= number <= 1:
        errors[field_name] = "Must be between 0 and 1."
        return DEFAULT_USER_PREFERENCES["scenic_priority"]
    return number


def _optional_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


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
