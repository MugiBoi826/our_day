import sqlite3
from pathlib import Path


def test_demo_has_room_layout_and_seating_preferences() -> None:
    database = (
        Path(__file__).parents[1]
        / "resources"
        / "demo"
        / "our_day_demo.db"
    )
    with sqlite3.connect(database) as connection:
        table_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(guest_tables)"
            )
        }
        guest_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(guests)"
            )
        }
        relation_table = connection.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type='table'
              AND name='guest_seating_preferences'
            """
        ).fetchone()[0]

    assert {
        "position_x",
        "position_y",
        "shape",
    }.issubset(table_columns)
    assert {
        "seating_notes",
        "accessibility_required",
    }.issubset(guest_columns)
    assert relation_table == 1
