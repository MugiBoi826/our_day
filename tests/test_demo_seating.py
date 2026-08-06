import sqlite3
from pathlib import Path


def test_demo_contains_assigned_and_unassigned_confirmed_guests() -> None:
    database_path = (
        Path(__file__).parents[1]
        / "resources"
        / "demo"
        / "our_day_demo.db"
    )

    with sqlite3.connect(database_path) as connection:
        assigned = connection.execute(
            """
            SELECT COUNT(*)
            FROM guests
            WHERE attendance_status = 'Részt vesz'
              AND table_id IS NOT NULL
            """
        ).fetchone()[0]

        unassigned = connection.execute(
            """
            SELECT COUNT(*)
            FROM guests
            WHERE attendance_status = 'Részt vesz'
              AND table_id IS NULL
            """
        ).fetchone()[0]

    assert assigned > 0
    assert unassigned > 0
