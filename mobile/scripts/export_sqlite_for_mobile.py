from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


TABLES = (
    "weddings",
    "entries",
    "tasks",
    "guest_tables",
    "invitation_groups",
    "guests",
    "guest_preferences",
    "guest_preference_rel",
    "guest_seating_preferences",
)


def export_database(source: Path, destination: Path) -> None:
    connection = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    payload = {
        "format": "our-day-sqlite-export",
        "version": 1,
        "tables": {
            table: [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
            for table in TABLES
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    export_database(args.source.resolve(), args.destination.resolve())
