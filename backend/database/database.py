"""SQLite connection, schema setup, and common database queries."""

from __future__ import annotations

import csv
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from .models import Landmark, SavedRoute, ScenicEdge

DEFAULT_DB_PATH = Path(__file__).with_name("scenic_routes.db")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS landmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'scenic',
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    scenic_score INTEGER NOT NULL DEFAULT 50 CHECK (scenic_score BETWEEN 0 AND 100),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scenic_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_node TEXT NOT NULL,
    end_node TEXT NOT NULL,
    distance_km REAL NOT NULL CHECK (distance_km >= 0),
    travel_time_min REAL NOT NULL CHECK (travel_time_min >= 0),
    scenic_score INTEGER NOT NULL CHECK (scenic_score BETWEEN 0 AND 100),
    road_name TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (start_node, end_node, road_name)
);

CREATE TABLE IF NOT EXISTS saved_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_location TEXT NOT NULL,
    end_location TEXT NOT NULL,
    theme TEXT NOT NULL DEFAULT 'balanced',
    route_json TEXT NOT NULL,
    scenic_score REAL NOT NULL DEFAULT 0,
    distance_km REAL NOT NULL DEFAULT 0,
    estimated_time_min REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_landmarks_category ON landmarks(category);
CREATE INDEX IF NOT EXISTS idx_edges_start_node ON scenic_edges(start_node);
CREATE INDEX IF NOT EXISTS idx_edges_end_node ON scenic_edges(end_node);
CREATE INDEX IF NOT EXISTS idx_saved_routes_created_at ON saved_routes(created_at);
"""


def get_database_path(db_path: str | Path | None = None) -> Path:
    """Return the SQLite file path, allowing tests or deployment to override it."""
    if db_path is not None:
        return Path(db_path)
    configured_path = os.environ.get("SCENIC_ROUTE_DB")
    return Path(configured_path) if configured_path else DEFAULT_DB_PATH


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with dictionary-like rows and foreign keys enabled."""
    database_path = get_database_path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@contextmanager
def database_session(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Commit on success and roll back on failure."""
    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path: str | Path | None = None) -> Path:
    """Create all required tables and indexes if they do not exist."""
    database_path = get_database_path(db_path)
    with database_session(database_path) as connection:
        connection.executescript(SCHEMA_SQL)
    return database_path


def _as_landmark(data: Landmark | Mapping[str, Any]) -> Landmark:
    if isinstance(data, Landmark):
        return data
    return Landmark(
        name=str(data["name"]),
        category=str(data.get("category", "scenic")),
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        description=str(data.get("description", "")),
        scenic_score=int(data.get("scenic_score", 50)),
    )


def _as_scenic_edge(data: ScenicEdge | Mapping[str, Any]) -> ScenicEdge:
    if isinstance(data, ScenicEdge):
        return data
    raw_tags = data.get("tags", ())
    if isinstance(raw_tags, str):
        tags = tuple(tag.strip().lower() for tag in raw_tags.split(",") if tag.strip())
    else:
        tags = tuple(str(tag).strip().lower() for tag in raw_tags if str(tag).strip())
    return ScenicEdge(
        start_node=str(data["start_node"]),
        end_node=str(data["end_node"]),
        distance_km=float(data["distance_km"]),
        travel_time_min=float(data["travel_time_min"]),
        scenic_score=int(data["scenic_score"]),
        road_name=str(data.get("road_name", "")),
        tags=tags,
    )


def insert_landmark(
    landmark: Landmark | Mapping[str, Any],
    db_path: str | Path | None = None,
) -> int:
    """Insert or replace a landmark and return its row id."""
    initialize_database(db_path)
    model = _as_landmark(landmark)
    with database_session(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO landmarks (
                name, category, latitude, longitude, description, scenic_score
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                category = excluded.category,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                description = excluded.description,
                scenic_score = excluded.scenic_score
            """,
            model.to_record(),
        )
        if cursor.lastrowid:
            return int(cursor.lastrowid)
        row = connection.execute(
            "SELECT id FROM landmarks WHERE name = ?",
            (model.name,),
        ).fetchone()
        return int(row["id"])


def list_landmarks(
    category: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return landmarks, optionally filtered by category."""
    initialize_database(db_path)
    query = "SELECT * FROM landmarks"
    params: tuple[Any, ...] = ()
    if category:
        query += " WHERE category = ?"
        params = (category,)
    query += " ORDER BY name"
    with database_session(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
    return [Landmark.from_row(row).to_dict() for row in rows]


def get_landmark_by_name(
    name: str,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Find one landmark by its exact name."""
    initialize_database(db_path)
    with database_session(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM landmarks WHERE name = ?",
            (name,),
        ).fetchone()
    return Landmark.from_row(row).to_dict() if row else None


def insert_scenic_edge(
    edge: ScenicEdge | Mapping[str, Any],
    db_path: str | Path | None = None,
) -> int:
    """Insert or replace a scenic road segment and return its row id."""
    initialize_database(db_path)
    model = _as_scenic_edge(edge)
    with database_session(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO scenic_edges (
                start_node, end_node, distance_km, travel_time_min,
                scenic_score, road_name, tags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(start_node, end_node, road_name) DO UPDATE SET
                distance_km = excluded.distance_km,
                travel_time_min = excluded.travel_time_min,
                scenic_score = excluded.scenic_score,
                tags = excluded.tags
            """,
            model.to_record(),
        )
        if cursor.lastrowid:
            return int(cursor.lastrowid)
        row = connection.execute(
            """
            SELECT id FROM scenic_edges
            WHERE start_node = ? AND end_node = ? AND road_name = ?
            """,
            (model.start_node, model.end_node, model.road_name),
        ).fetchone()
        return int(row["id"])


def list_scenic_edges(
    start_node: str | None = None,
    end_node: str | None = None,
    min_scenic_score: int | None = None,
    tag: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return scenic road segments with optional filters."""
    initialize_database(db_path)
    filters: list[str] = []
    params: list[Any] = []

    if start_node:
        filters.append("start_node = ?")
        params.append(start_node)
    if end_node:
        filters.append("end_node = ?")
        params.append(end_node)
    if min_scenic_score is not None:
        filters.append("scenic_score >= ?")
        params.append(min_scenic_score)

    query = "SELECT * FROM scenic_edges"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY start_node, end_node, road_name"

    with database_session(db_path) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()

    edges = [ScenicEdge.from_row(row).to_dict() for row in rows]
    if tag:
        normalized_tag = tag.strip().lower()
        edges = [edge for edge in edges if normalized_tag in edge["tags"]]
    return edges


def save_route(
    route: SavedRoute | Mapping[str, Any],
    db_path: str | Path | None = None,
) -> int:
    """Save a generated route summary and return its row id."""
    initialize_database(db_path)
    model = route if isinstance(route, SavedRoute) else SavedRoute.from_mapping(route)
    with database_session(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO saved_routes (
                start_location, end_location, theme, route_json,
                scenic_score, distance_km, estimated_time_min
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            model.to_record(),
        )
        return int(cursor.lastrowid)


def get_saved_route(
    route_id: int,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Return a saved route by id, or None when it does not exist."""
    initialize_database(db_path)
    with database_session(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM saved_routes WHERE id = ?",
            (route_id,),
        ).fetchone()
    return SavedRoute.from_row(row).to_dict() if row else None


def list_saved_routes(
    limit: int = 20,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return recently saved routes."""
    initialize_database(db_path)
    safe_limit = max(1, min(int(limit), 100))
    with database_session(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM saved_routes
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return [SavedRoute.from_row(row).to_dict() for row in rows]


def seed_landmarks_from_json(
    json_path: str | Path,
    db_path: str | Path | None = None,
) -> int:
    """Load landmarks from a JSON list and return the number of records processed."""
    with Path(json_path).open("r", encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, list):
        raise ValueError("Landmark seed file must contain a JSON list.")
    for record in records:
        insert_landmark(record, db_path)
    return len(records)


def seed_edges_from_csv(
    csv_path: str | Path,
    db_path: str | Path | None = None,
) -> int:
    """Load scenic edge rows from CSV and return the number of records processed."""
    count = 0
    with Path(csv_path).open("r", encoding="utf-8", newline="") as file:
        for record in csv.DictReader(file):
            insert_scenic_edge(record, db_path)
            count += 1
    return count
