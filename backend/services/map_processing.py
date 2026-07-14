"""Map payload processing for generated scenic routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from database import list_landmarks


class MapProcessingError(ValueError):
    """Raised when route data cannot be converted into a map payload."""

    def __init__(self, message: str, errors: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

    def to_dict(self) -> dict[str, Any]:
        return {"message": self.message, "errors": self.errors}


def build_map_payload(
    route: Mapping[str, Any],
    landmarks: list[Mapping[str, Any]] | None = None,
    db_path: str | Path | None = None,
    *,
    include_landmarks: bool = True,
) -> dict[str, Any]:
    """Build coordinates, markers, bounds, and GeoJSON for frontend maps."""
    landmark_records = landmarks if landmarks is not None else list_landmarks(db_path=db_path)
    landmark_index = _index_landmarks(landmark_records)
    route_coordinates = _route_coordinates(route, landmark_index)

    if not route_coordinates:
        raise MapProcessingError(
            "Route does not contain mappable coordinates.",
            {"route": "Route nodes must match landmarks with latitude and longitude."},
        )

    markers = _route_markers(route_coordinates)
    if include_landmarks:
        markers.extend(_nearby_landmark_markers(landmark_records, route_coordinates))

    geojson = route_to_geojson(route, landmark_records)
    bounds = calculate_bounds(route_coordinates)

    return {
        "center": calculate_center(route_coordinates),
        "bounds": bounds,
        "route_coordinates": route_coordinates,
        "markers": markers,
        "geojson": geojson,
    }


def route_to_geojson(
    route: Mapping[str, Any],
    landmarks: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Convert a generated route into a GeoJSON FeatureCollection."""
    landmark_index = _index_landmarks(landmarks or [])
    route_coordinates = _route_coordinates(route, landmark_index)
    line_coordinates = [
        [point["longitude"], point["latitude"]] for point in route_coordinates
    ]
    features: list[dict[str, Any]] = []

    if len(line_coordinates) >= 2:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": line_coordinates,
                },
                "properties": {
                    "kind": "route",
                    "start_node": route.get("start_node"),
                    "end_node": route.get("end_node"),
                    **dict(route.get("summary", {})),
                },
            }
        )

    features.extend(_segment_features(route, landmark_index))
    features.extend(_marker_features(_route_markers(route_coordinates)))

    return {"type": "FeatureCollection", "features": features}


def calculate_bounds(points: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate southwest and northeast bounds for a set of coordinates."""
    point_list = list(points)
    if not point_list:
        raise MapProcessingError(
            "Cannot calculate map bounds without coordinates.",
            {"coordinates": "At least one coordinate is required."},
        )

    latitudes = [float(point["latitude"]) for point in point_list]
    longitudes = [float(point["longitude"]) for point in point_list]

    return {
        "southwest": {
            "latitude": min(latitudes),
            "longitude": min(longitudes),
        },
        "northeast": {
            "latitude": max(latitudes),
            "longitude": max(longitudes),
        },
    }


def calculate_center(points: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    """Calculate a center point for fitting a map view."""
    bounds = calculate_bounds(points)
    return {
        "latitude": round(
            (bounds["southwest"]["latitude"] + bounds["northeast"]["latitude"]) / 2,
            6,
        ),
        "longitude": round(
            (bounds["southwest"]["longitude"] + bounds["northeast"]["longitude"]) / 2,
            6,
        ),
    }


def _route_coordinates(
    route: Mapping[str, Any],
    landmark_index: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    coordinates: list[dict[str, Any]] = []
    for node_id in route.get("nodes", []):
        landmark = landmark_index.get(str(node_id).lower())
        if not landmark:
            continue
        coordinates.append(
            {
                "node_id": str(node_id),
                "name": str(landmark["name"]),
                "latitude": float(landmark["latitude"]),
                "longitude": float(landmark["longitude"]),
                "category": landmark.get("category", "scenic"),
                "scenic_score": landmark.get("scenic_score", 50),
            }
        )
    return coordinates


def _segment_features(
    route: Mapping[str, Any],
    landmark_index: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []

    for index, segment in enumerate(route.get("segments", []), start=1):
        geometry = _segment_geometry(segment, landmark_index)
        if len(geometry) < 2:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": geometry,
                },
                "properties": {
                    "kind": "segment",
                    "sequence": index,
                    "start_node": segment.get("start_node"),
                    "end_node": segment.get("end_node"),
                    "road_name": segment.get("road_name", ""),
                    "distance_km": segment.get("distance_km", 0),
                    "travel_time_min": segment.get("travel_time_min", 0),
                    "scenic_score": segment.get("scenic_score", 0),
                    "tags": list(segment.get("tags", [])),
                },
            }
        )

    return features


def _segment_geometry(
    segment: Mapping[str, Any],
    landmark_index: Mapping[str, Mapping[str, Any]],
) -> list[list[float]]:
    geometry = segment.get("geometry")
    if isinstance(geometry, list) and geometry:
        normalized = [_normalize_geojson_coordinate(point) for point in geometry]
        return [point for point in normalized if point]

    start = landmark_index.get(str(segment.get("start_node", "")).lower())
    end = landmark_index.get(str(segment.get("end_node", "")).lower())
    if not start or not end:
        return []

    return [
        [float(start["longitude"]), float(start["latitude"])],
        [float(end["longitude"]), float(end["latitude"])],
    ]


def _normalize_geojson_coordinate(value: Any) -> list[float]:
    if isinstance(value, Mapping):
        if "longitude" in value and "latitude" in value:
            return [float(value["longitude"]), float(value["latitude"])]
        if "lng" in value and "lat" in value:
            return [float(value["lng"]), float(value["lat"])]
        if "lon" in value and "lat" in value:
            return [float(value["lon"]), float(value["lat"])]
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return [float(value[0]), float(value[1])]
    return []


def _route_markers(route_coordinates: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    last_index = len(route_coordinates) - 1
    for index, point in enumerate(route_coordinates):
        if index == 0:
            marker_type = "start"
        elif index == last_index:
            marker_type = "destination"
        else:
            marker_type = "waypoint"

        markers.append(
            {
                "type": marker_type,
                "node_id": point["node_id"],
                "name": point["name"],
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "sequence": index + 1,
            }
        )
    return markers


def _nearby_landmark_markers(
    landmarks: list[Mapping[str, Any]],
    route_coordinates: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    route_node_names = {point["name"].lower() for point in route_coordinates}
    markers: list[dict[str, Any]] = []

    for landmark in landmarks:
        name = str(landmark["name"])
        if name.lower() in route_node_names:
            continue
        markers.append(
            {
                "type": "landmark",
                "node_id": name,
                "name": name,
                "latitude": float(landmark["latitude"]),
                "longitude": float(landmark["longitude"]),
                "category": landmark.get("category", "scenic"),
                "scenic_score": landmark.get("scenic_score", 50),
            }
        )

    return markers


def _marker_features(markers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [marker["longitude"], marker["latitude"]],
            },
            "properties": {
                key: value
                for key, value in marker.items()
                if key not in {"latitude", "longitude"}
            },
        }
        for marker in markers
    ]


def _index_landmarks(
    landmarks: list[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    return {str(landmark["name"]).lower(): landmark for landmark in landmarks}
