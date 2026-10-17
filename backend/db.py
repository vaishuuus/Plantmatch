"""
Tiny SQLite 'notebook' for real user feedback (sqlite3 comes with Python, nothing to install).
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "plantmatch.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create the feedback table if it isn't there yet."""
    conn = _connect()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,        -- one id per 'Find my plants' click
                plant_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,      -- 5 = thumbs up, 1 = thumbs down
                light INTEGER, water INTEGER, humidity INTEGER,
                size INTEGER, effort INTEGER, pets INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (room_id, plant_id)    -- one vote per plant per search
            )""")
        conn.commit()
    finally:
        conn.close()


def add_feedback(room_id, plant_id, rating, u):
    """Save a vote. If the same room already voted on this plant, update it."""
    conn = _connect()
    try:
        conn.execute("""
            INSERT INTO feedback (room_id, plant_id, rating, light, water, humidity, size, effort, pets)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (room_id, plant_id)
            DO UPDATE SET rating = excluded.rating, created_at = CURRENT_TIMESTAMP
        """, (room_id, plant_id, rating, u["light"], u["water"], u["humidity"],
              u["size"], u["effort"], int(u["pets"])))
        conn.commit()
    finally:
        conn.close()


def load_feedback():
    """All votes as a pandas table."""
    conn = _connect()
    try:
        return pd.read_sql_query(
            "SELECT room_id, plant_id, rating, light, water, humidity, size, effort, pets FROM feedback",
            conn)
    finally:
        conn.close()


def count_feedback():
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    finally:
        conn.close()