from __future__ import annotations

from pathlib import Path
import sqlite3

from our_day.database.connection import (
    DATABASE_PATH,
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
    )

    @classmethod
    def clear_database(cls) -> Path:
        initialize_database()

        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")

            for table_name in cls.CLEAR_ORDER:
                connection.execute(
                    f"DELETE FROM {table_name}"
                )

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
                    'guest_preferences'
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

        initialize_database()

        with sqlite3.connect(demo_database) as source_connection:
            with sqlite3.connect(DATABASE_PATH) as target_connection:
                source_connection.backup(target_connection)
                target_connection.commit()

        initialize_database()
        return DATABASE_PATH
