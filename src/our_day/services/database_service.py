from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

from our_day.database.connection import (
    DATABASE_PATH,
    DATA_DIR,
    get_demo_database_path,
    initialize_database,
)


class DatabaseService:
    CLEAR_ORDER = (
        "guest_preference_rel",
        "guests",
        "invitation_groups",
        "guest_tables",
        "tasks",
        "entries",
        "guest_preferences",
        "weddings",
    )

    REQUIRED_TABLES = {
        "entries",
        "tasks",
        "guests",
        "guest_tables",
        "guest_preferences",
        "guest_preference_rel",
        "invitation_groups",
        "weddings",
    }

    @classmethod
    def clear_database(cls) -> Path:
        initialize_database()

        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")

            for table_name in cls.CLEAR_ORDER:
                connection.execute(f"DELETE FROM {table_name}")

            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name IN (
                    'guest_preference_rel',
                    'guests',
                    'invitation_groups',
                    'guest_tables',
                    'tasks',
                    'entries',
                    'guest_preferences',
                    'weddings'
                )
                """
            )

            connection.commit()
            connection.execute("PRAGMA foreign_keys = ON")

        initialize_database()
        return DATABASE_PATH

    @staticmethod
    def load_demo_database() -> Path:
        demo_database = get_demo_database_path()

        if not demo_database.exists():
            raise FileNotFoundError(
                f"A demóadatbázis nem található: {demo_database}"
            )

        DatabaseService._restore_database(demo_database)
        initialize_database()
        return DATABASE_PATH

    @staticmethod
    def export_database(destination: str | Path) -> Path:
        initialize_database()

        destination_path = Path(destination)
        if destination_path.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
            destination_path = destination_path.with_suffix(".db")

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if destination_path.resolve() == DATABASE_PATH.resolve():
            raise ValueError(
                "Az export célja nem lehet az aktív adatbázisfájl."
            )

        with sqlite3.connect(DATABASE_PATH) as source_connection:
            with sqlite3.connect(destination_path) as target_connection:
                source_connection.backup(target_connection)
                target_connection.commit()

        return destination_path

    @classmethod
    def import_database(cls, source: str | Path) -> tuple[Path, Path]:
        source_path = Path(source)

        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(
                f"Az importálandó adatbázis nem található: {source_path}"
            )

        if source_path.resolve() == DATABASE_PATH.resolve():
            raise ValueError("Az aktív adatbázis önmagából nem importálható.")

        cls._validate_database(source_path)
        backup_path = cls.create_automatic_backup("import_before")
        cls._restore_database(source_path)
        initialize_database()
        return DATABASE_PATH, backup_path

    @staticmethod
    def create_automatic_backup(prefix: str = "backup") -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_directory = DATA_DIR / "backups"
        backup_directory.mkdir(parents=True, exist_ok=True)
        backup_path = backup_directory / f"our_day_{prefix}_{timestamp}.db"
        return DatabaseService.export_database(backup_path)

    @classmethod
    def _validate_database(cls, database_path: Path) -> None:
        try:
            with sqlite3.connect(
                f"file:{database_path.as_posix()}?mode=ro",
                uri=True,
            ) as connection:
                integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()

                if not integrity or str(integrity[0]).lower() != "ok":
                    raise ValueError(
                        "Az adatbázis sérült vagy az integritás-ellenőrzés sikertelen."
                    )

                existing_tables = {
                    str(row[0])
                    for row in connection.execute(
                        """
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                        """
                    )
                }
        except sqlite3.DatabaseError as error:
            raise ValueError(
                "A kiválasztott fájl nem érvényes SQLite-adatbázis."
            ) from error

        missing_tables = cls.REQUIRED_TABLES - existing_tables
        if missing_tables:
            raise ValueError(
                "A fájl nem megfelelő Our Day adatbázis. "
                f"Hiányzó táblák: {', '.join(sorted(missing_tables))}"
            )

    @staticmethod
    def _restore_database(source_database: Path) -> None:
        initialize_database()

        with sqlite3.connect(source_database) as source_connection:
            with sqlite3.connect(DATABASE_PATH) as target_connection:
                source_connection.backup(target_connection)
                target_connection.commit()
