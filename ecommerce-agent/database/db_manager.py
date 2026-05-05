"""SQLite database manager for the Marketing AI Agent system."""

import sqlite3
import os
from .schema import SCHEMA


class SQLiteManager:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self):
        conn = self.get_conn()
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()

    def execute(self, query: str, params: tuple = ()):
        conn = self.get_conn()
        cur = conn.execute(query, params)
        conn.commit()
        conn.close()
        return cur

    def fetch_all(self, query: str, params: tuple = ()):
        conn = self.get_conn()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def fetch_one(self, query: str, params: tuple = ()):
        conn = self.get_conn()
        row = conn.execute(query, params).fetchone()
        conn.close()
        return dict(row) if row else None

    def insert(self, table: str, data: dict):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = tuple(data.values())
        cur = self.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values
        )
        return cur.lastrowid

    def insert_many(self, table: str, rows: list[dict]):
        if not rows:
            return
        columns = ", ".join(rows[0].keys())
        placeholders = ", ".join(["?"] * len(rows[0]))
        conn = self.get_conn()
        conn.executemany(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            [tuple(r.values()) for r in rows],
        )
        conn.commit()
        conn.close()

    def table_count(self, table: str) -> int:
        row = self.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
        return row["cnt"] if row else 0

    def is_empty(self) -> bool:
        return self.table_count("products") == 0
