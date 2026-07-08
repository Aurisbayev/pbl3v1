"""Navigation request processing for scenic route generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from backend.database import (
    get_landmark_by_name,
    list_landmarks,
    list_scenic_edges,
    save_route,
)
from backend.utils.graph_utils import find_scenic_path, nearest_node
from backend.utils.helpers import clamp_score, clean_string
from backend.utils.validation import validate_route_request


HIGHWAY_TAGS = {"highway", "motorway", "expressway", "freeway"}

THEME_TAGS: dict[str, tuple[str, ...]] = {
    "balanced": (),
    "nature": ("nature", "park", "garden", "forest", "trail", "mountain"),
    "historic": ("historic", "heritage", "temple", "shrine", "museum", "old-town"),
    "waterfront": ("waterfront", "river", "lake", "canal", "coast", "bridge"),
    "city": ("city", "shopping", "architecture", "night-view", "station", "downtown"),
    "custom": (),
}


class NavigationProcessingError(ValueError):
    """Raised when a route request is valid but cannot be processed."""

    def __init__(self, message: str, errors: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

    def to_dict(self) -> dict[str, Any]:
        return {"message": self.message, "errors": self.errors}


def generate_navigation_route(
    payload: Mapping[str, Any] | None,
    db_path: str | Path | None = None,
    *,
    save_generated_route: bool = True,
    directed: bool = False,
) -> dict[str, Any]:
    """Validate a request, generate a scenic path, and return navigation data."""
    request = validate_route_request(payload)
    landmarks = list_landmarks(db_path=db_path)
    edges = list_scenic_edges(db_path=db_path)

    if not edges:
        raise NavigationProcessingError(
            "No scenic road segments are available.",
            {"edges": "Add scenic_edges records before generating a route."},
        )

    graph_nodes = _collect_graph_nodes(edges)
    start = resolve_route_location(
        request["start_location"],
        landmarks,
        graph_nodes=graph_nodes,
    )
    destination = resolve_route_location(
        request["end_location"],
        landmarks,
        graph_nodes=graph_nodes,
    )

    if start["node_id"] == destination["node_id"]:
        raise NavigationProcessingError(
            "Start and destination resolve to the same route node.",
            {"end_location": "Choose a destination farther away from the start."},
        )

    candidate_edges = _prepare_edges_for_preferences(edges, request)
    route = find_scenic_path(
        candidate_edges,
        start["node_id"],
        destination["node_id"],
        scenic_priority=request["scenic_priority"],
        directed=directed,
    )

    if not route["segments"]:
        raise NavigationProcessingError(
            "No route could be found between those locations.",
            {
                "start_location": start["node_id"],
                "end_location": destination["node_id"],
            },
        )

    summary = route["summary"]
    max_distance_km = request.get("max_distance_km")
    within_max_distance = (
        max_distance_km is None or summary["distance_km"] <= float(max_distance_km)
    )

    route.update(
        {
            "start_location": request["start_location"],
            "end_location": request["end_location"],
            "resolved_start": start,
            "resolved_end": destination,
            "theme": request["theme"],
            "preferred_tags": _combined_preferred_tags(request),
            "within_max_distance": within_max_distance,
        }
    )
    if max_distance_km is not None:
        route["max_distance_km"] = max_distance_km

    saved_route_id = None
    if save_generated_route:
        saved_route_id = save_route(
            {
                "start_location": request["start_location"],
                "end_location": request["end_location"],
                "theme": request["theme"],
                "route": route,
                "scenic_score": summary["scenic_score"],
                "distance_km": summary["distance_km"],
                "estimated_time_min": summary["estimated_time_min"],
            },
            db_path=db_path,
        )

    return {
        "route": route,
        "summary": summary,
        "saved_route_id": saved_route_id,
        "warnings": _route_warnings(route),
    }


def resolve_route_location(
    location: str,
    landmarks: list[Mapping[str, Any]] | None = None,
    *,
    graph_nodes: set[str] | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve a user-entered place name or coordinate into a route node id."""
    cleaned_location = clean_string(location)
    if not cleaned_location:
        raise NavigationProcessingError(
            "Location is required.",
            {"location": "Enter a place name or latitude,longitude pair."},
        )

    graph_nodes = graph_nodes or set()
    if cleaned_location in graph_nodes:
        return {
            "input": cleaned_location,
            "node_id": cleaned_location,
            "match_type": "node",
        }

    case_match = _case_insensitive_node_match(cleaned_location, graph_nodes)
    if case_match:
        return {
            "input": cleaned_location,
            "node_id": case_match,
            "match_type": "node",
        }

    landmark_records = landmarks if landmarks is not None else list_landmarks(db_path=db_path)
    landmark = _find_landmark(cleaned_location, landmark_records, db_path)
    if landmark:
        node_id = _landmark_node_id(landmark, graph_nodes)
        if not node_id:
            raise NavigationProcessingError(
                "Landmark exists but is not connected to the route graph.",
                {"location": cleaned_location},
            )
        return _landmark_to_location(cleaned_location, landmark, "landmark", node_id)

    coordinates = _parse_coordinate_pair(cleaned_location)
    if coordinates and landmark_records:
        candidate_landmarks = _route_ready_landmarks(landmark_records, graph_nodes)
        nearest = nearest_node(
            candidate_landmarks,
            coordinates["latitude"],
            coordinates["longitude"],
        )
        if nearest:
            node_id = _landmark_node_id(nearest, graph_nodes) or str(nearest["name"])
            resolved = _landmark_to_location(
                cleaned_location,
                nearest,
                "nearest_landmark",
                node_id,
            )
            resolved["requested_coordinate"] = coordinates
            return resolved

    raise NavigationProcessingError(
        "Location could not be matched to a route node.",
        {"location": cleaned_location},
    )


def _prepare_edges_for_preferences(
    edges: list[Mapping[str, Any]],
    request: Mapping[str, Any],
) -> list[dict[str, Any]]:
    preferred_tags = set(_combined_preferred_tags(request))
    prepared_edges: list[dict[str, Any]] = []

    for edge in edges:
        normalized = dict(edge)
        edge_tags = _edge_tags(edge)
        if request.get("avoid_highways") and edge_tags.intersection(HIGHWAY_TAGS):
            continue

        if preferred_tags and edge_tags.intersection(preferred_tags):
            normalized["scenic_score"] = clamp_score(
                float(edge.get("scenic_score", 0)) + _tag_bonus(edge_tags, preferred_tags)
            )

        prepared_edges.append(normalized)

    return prepared_edges


def _combined_preferred_tags(request: Mapping[str, Any]) -> list[str]:
    tags: list[str] = []
    theme = clean_string(request.get("theme", "balanced")).lower() or "balanced"
    for tag in THEME_TAGS.get(theme, ()):
        if tag not in tags:
            tags.append(tag)
    for tag in request.get("preferred_tags", []):
        normalized = clean_string(tag).lower()
        if normalized and normalized not in tags:
            tags.append(normalized)
    return tags


def _tag_bonus(edge_tags: set[str], preferred_tags: set[str]) -> int:
    match_count = len(edge_tags.intersection(preferred_tags))
    return min(25, 10 + (match_count - 1) * 5)


def _edge_tags(edge: Mapping[str, Any]) -> set[str]:
    tags = edge.get("tags", [])
    if isinstance(tags, str):
        tags = tags.split(",")
    return {clean_string(tag).lower() for tag in tags if clean_string(tag)}


def _collect_graph_nodes(edges: list[Mapping[str, Any]]) -> set[str]:
    nodes: set[str] = set()
    for edge in edges:
        nodes.add(str(edge["start_node"]))
        nodes.add(str(edge["end_node"]))
    return nodes


def _find_landmark(
    location: str,
    landmarks: list[Mapping[str, Any]],
    db_path: str | Path | None,
) -> Mapping[str, Any] | None:
    for landmark in landmarks:
        if clean_string(landmark.get("name", "")).lower() == location.lower():
            return landmark

    stored_landmark = get_landmark_by_name(location, db_path=db_path)
    return stored_landmark if stored_landmark else None


def _landmark_to_location(
    original_input: str,
    landmark: Mapping[str, Any],
    match_type: str,
    node_id: str,
) -> dict[str, Any]:
    return {
        "input": original_input,
        "node_id": node_id,
        "match_type": match_type,
        "latitude": float(landmark["latitude"]),
        "longitude": float(landmark["longitude"]),
        "category": landmark.get("category", "scenic"),
        "scenic_score": landmark.get("scenic_score", 50),
    }


def _parse_coordinate_pair(value: str) -> dict[str, float] | None:
    separators = (",", " ")
    parts: list[str] = []
    for separator in separators:
        if separator in value:
            parts = [part for part in value.split(separator) if part]
            break

    if len(parts) != 2:
        return None

    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return None

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None

    return {"latitude": latitude, "longitude": longitude}


def _case_insensitive_node_match(location: str, graph_nodes: set[str]) -> str | None:
    location_lower = location.lower()
    for node in graph_nodes:
        if node.lower() == location_lower:
            return node
    return None


def _landmark_node_id(
    landmark: Mapping[str, Any],
    graph_nodes: set[str],
) -> str | None:
    landmark_name = str(landmark["name"])
    if not graph_nodes:
        return landmark_name
    return _case_insensitive_node_match(landmark_name, graph_nodes)


def _route_ready_landmarks(
    landmarks: list[Mapping[str, Any]],
    graph_nodes: set[str],
) -> list[Mapping[str, Any]]:
    if not graph_nodes:
        return landmarks
    return [
        landmark
        for landmark in landmarks
        if _case_insensitive_node_match(str(landmark["name"]), graph_nodes)
    ]


def _route_warnings(route: Mapping[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not route.get("within_max_distance", True):
        warnings.append("Generated route is longer than max_distance_km.")
    return warnings
