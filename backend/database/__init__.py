"""Database helpers for the Scenic Route Planner backend."""

from .database import (
    get_connection,
    get_database_path,
    get_landmark_by_name,
    get_saved_route,
    initialize_database,
    insert_landmark,
    insert_scenic_edge,
    list_landmarks,
    list_saved_routes,
    list_scenic_edges,
    save_route,
)

__all__ = [
    "get_connection",
    "get_database_path",
    "get_landmark_by_name",
    "get_saved_route",
    "initialize_database",
    "insert_landmark",
    "insert_scenic_edge",
    "list_landmarks",
    "list_saved_routes",
    "list_scenic_edges",
    "save_route",
]
