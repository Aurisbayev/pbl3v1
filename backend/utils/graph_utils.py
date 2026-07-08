"""Graph utilities for scenic route generation."""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Any, Mapping

from .helpers import clamp, haversine_distance_km, round_route_number


def _value(edge: Any, key: str, default: Any = None) -> Any:
    if isinstance(edge, Mapping):
        return edge.get(key, default)
    return getattr(edge, key, default)


def _normalize_segment(edge: Any, reverse: bool = False) -> dict[str, Any]:
    start_node = str(_value(edge, "start_node"))
    end_node = str(_value(edge, "end_node"))
    tags = _value(edge, "tags", [])
    if isinstance(tags, str):
        tags = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]

    segment = {
        "start_node": end_node if reverse else start_node,
        "end_node": start_node if reverse else end_node,
        "distance_km": float(_value(edge, "distance_km", 0)),
        "travel_time_min": float(_value(edge, "travel_time_min", 0)),
        "scenic_score": int(_value(edge, "scenic_score", 0)),
        "road_name": str(_value(edge, "road_name", "")),
        "tags": list(tags),
    }
    return segment


def build_adjacency_list(
    edges: list[Any],
    directed: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    """Build an adjacency list from scenic edge records."""
    graph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        segment = _normalize_segment(edge)
        graph[segment["start_node"]].append(segment)
        graph.setdefault(segment["end_node"], [])
        if not directed:
            reversed_segment = _normalize_segment(edge, reverse=True)
            graph[reversed_segment["start_node"]].append(reversed_segment)
    return dict(graph)


def calculate_edge_cost(
    segment: Mapping[str, Any],
    scenic_priority: float = 0.6,
) -> float:
    """Cost used by pathfinding, balancing short distance against scenic value."""
    priority = clamp(float(scenic_priority), 0, 1)
    distance = max(float(segment.get("distance_km", 0)), 0.001)
    scenic_ratio = clamp(float(segment.get("scenic_score", 0)) / 100, 0, 1)

    distance_cost = distance * (1 - priority)
    scenic_cost = distance * (1 - scenic_ratio) * priority
    return max(distance_cost + scenic_cost, 0.001)


def find_scenic_path(
    edges: list[Any],
    start_node: str,
    end_node: str,
    scenic_priority: float = 0.6,
    directed: bool = False,
) -> dict[str, Any]:
    """Find a scenic path with Dijkstra's algorithm."""
    graph = build_adjacency_list(edges, directed=directed)
    start = str(start_node)
    destination = str(end_node)

    if start not in graph or destination not in graph:
        return _empty_route(start, destination)

    distances: dict[str, float] = {node: float("inf") for node in graph}
    previous: dict[str, tuple[str, dict[str, Any]]] = {}
    distances[start] = 0
    queue: list[tuple[float, str]] = [(0, start)]

    while queue:
        current_cost, current_node = heapq.heappop(queue)
        if current_node == destination:
            break
        if current_cost > distances[current_node]:
            continue

        for segment in graph[current_node]:
            neighbor = segment["end_node"]
            new_cost = current_cost + calculate_edge_cost(segment, scenic_priority)
            if new_cost < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_cost
                previous[neighbor] = (current_node, segment)
                heapq.heappush(queue, (new_cost, neighbor))

    if destination not in previous and start != destination:
        return _empty_route(start, destination)

    segments = _reconstruct_segments(previous, start, destination)
    nodes = [start] + [segment["end_node"] for segment in segments]
    return {
        "start_node": start,
        "end_node": destination,
        "nodes": nodes,
        "segments": segments,
        "summary": calculate_route_totals(segments),
    }


def _reconstruct_segments(
    previous: dict[str, tuple[str, dict[str, Any]]],
    start: str,
    destination: str,
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    current = destination
    while current != start:
        previous_node, segment = previous[current]
        segments.append(segment)
        current = previous_node
    segments.reverse()
    return segments


def _empty_route(start_node: str, end_node: str) -> dict[str, Any]:
    return {
        "start_node": start_node,
        "end_node": end_node,
        "nodes": [],
        "segments": [],
        "summary": calculate_route_totals([]),
    }


def calculate_route_totals(segments: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate total distance, time, and weighted scenic score."""
    total_distance = sum(float(segment.get("distance_km", 0)) for segment in segments)
    total_time = sum(float(segment.get("travel_time_min", 0)) for segment in segments)

    if total_distance > 0:
        weighted_score = sum(
            float(segment.get("distance_km", 0)) * float(segment.get("scenic_score", 0))
            for segment in segments
        ) / total_distance
    elif segments:
        weighted_score = sum(float(segment.get("scenic_score", 0)) for segment in segments)
        weighted_score /= len(segments)
    else:
        weighted_score = 0

    return {
        "distance_km": round_route_number(total_distance),
        "estimated_time_min": round_route_number(total_time),
        "scenic_score": round_route_number(weighted_score),
        "segment_count": len(segments),
    }


def filter_edges_by_tags(
    edges: list[Mapping[str, Any]],
    preferred_tags: list[str],
) -> list[Mapping[str, Any]]:
    """Keep edges that match at least one preferred tag."""
    if not preferred_tags:
        return edges
    normalized_tags = {tag.strip().lower() for tag in preferred_tags if tag.strip()}
    return [
        edge
        for edge in edges
        if normalized_tags.intersection({str(tag).lower() for tag in edge.get("tags", [])})
    ]


def nearest_node(
    nodes: list[Mapping[str, Any]],
    latitude: float,
    longitude: float,
) -> Mapping[str, Any] | None:
    """Find the nearest node or landmark to the provided coordinates."""
    if not nodes:
        return None
    return min(
        nodes,
        key=lambda node: haversine_distance_km(
            latitude,
            longitude,
            float(node["latitude"]),
            float(node["longitude"]),
        ),
    )
