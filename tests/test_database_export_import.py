from pathlib import Path
import sqlite3

from our_day.database import connection as database_connection
from our_day.services.database_service import DatabaseService


def test_database_export_and_import(tmp_path: Path) -> None:
    active = tmp_path / "active.db"
    database_connection.DATA_DIR = tmp_path
    database_connection.DATABASE_PATH = active

    import our_day.services.database_service as database_service_module
    database_service_module.DATA_DIR = tmp_path
    database_service_module.DATABASE_PATH = active

    database_connection.initialize_database()

    with sqlite3.connect(active) as connection:
        connection.execute(
            "INSERT INTO tasks(title, status) VALUES (?, ?)",
            ("Export teszt", "Teendő"),
        )
        connection.commit()

    exported = DatabaseService.export_database(tmp_path / "export.db")

    with sqlite3.connect(active) as connection:
        connection.execute("DELETE FROM tasks")
        connection.commit()

    DatabaseService.import_database(exported)

    with sqlite3.connect(active) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM tasks WHERE title = ?",
            ("Export teszt",),
        ).fetchone()[0]

    assert count == 1
