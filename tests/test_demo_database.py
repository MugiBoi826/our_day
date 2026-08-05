import sqlite3
from pathlib import Path


def test_demo_database_contains_data():
    path = Path(__file__).parents[1] / "resources" / "demo" / "our_day_demo.db"
    assert path.exists()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM guests").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM invitation_groups").fetchone()[0] > 0
