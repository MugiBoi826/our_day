from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import sys


APPLICATION_FOLDER_NAME = "Our Day"
DATABASE_FILE_NAME = "our_day.db"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_bundle_root() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return get_project_root()


def get_data_directory() -> Path:
    override = os.environ.get("OUR_DAY_DATA_DIR")

    if override:
        return Path(override).expanduser().resolve()

    if is_frozen():
        local_app_data = os.environ.get("LOCALAPPDATA")

        if local_app_data:
            return Path(local_app_data) / APPLICATION_FOLDER_NAME / "data"

        return (
            Path.home()
            / "AppData"
            / "Local"
            / APPLICATION_FOLDER_NAME
            / "data"
        )

    return get_project_root() / "data"


def get_database_path() -> Path:
    return get_data_directory() / DATABASE_FILE_NAME


def get_demo_database_path() -> Path:
    return (
        get_bundle_root()
        / "resources"
        / "demo"
        / "our_day_demo.db"
    )


DATA_DIR = get_data_directory()
DATABASE_PATH = get_database_path()


def ensure_database_exists() -> None:
    # SQLite creates the file on first connection. The bundled demo database
    # is loaded only when the user explicitly selects it in Settings.
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_database_exists()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _column_exists(
    connection: sqlite3.Connection,
    table: str,
    column: str,
) -> bool:
    return any(
        row["name"] == column
        for row in connection.execute(
            f"PRAGMA table_info({table})"
        )
    )


def initialize_database() -> None:
    ensure_database_exists()

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS weddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bride_name TEXT,
                groom_name TEXT,
                wedding_date TEXT,
                venue_name TEXT,
                venue_address TEXT,
                budget_amount REAL NOT NULL DEFAULT 0,
                notes TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                contact_name TEXT,
                phone TEXT,
                email TEXT,
                deposit_amount REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Ötlet',
                deposit_due_date TEXT,
                deposit_paid_date TEXT,
                payment_due_date TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for name in (
            "deposit_due_date",
            "deposit_paid_date",
            "payment_due_date",
        ):
            if not _column_exists(
                connection,
                "entries",
                name,
            ):
                connection.execute(
                    f"ALTER TABLE entries ADD COLUMN {name} TEXT"
                )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'Közepes',
                status TEXT NOT NULL DEFAULT 'Teendő',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                guest_type TEXT NOT NULL DEFAULT 'Felnőtt',
                invitation_status TEXT NOT NULL DEFAULT 'Tervezett',
                attendance_status TEXT NOT NULL DEFAULT 'Válaszra vár',
                has_plus_one INTEGER NOT NULL DEFAULT 0,
                plus_one_name TEXT,
                attends_dinner INTEGER NOT NULL DEFAULT 1,
                dietary_notes TEXT,
                table_name TEXT,
                table_id INTEGER,
                parent_guest_id INTEGER,
                family_group_id INTEGER,
                family_name TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        guest_columns = {
            "table_id": "INTEGER",
            "parent_guest_id": "INTEGER",
            "family_group_id": "INTEGER",
            "family_name": "TEXT",
            "invitation_group_id": "INTEGER",
            "response_date": "TEXT",
            "is_contact_person": "INTEGER NOT NULL DEFAULT 0",
        }

        for column, column_type in guest_columns.items():
            if not _column_exists(
                connection,
                "guests",
                column,
            ):
                connection.execute(
                    f"""
                    ALTER TABLE guests
                    ADD COLUMN {column} {column_type}
                    """
                )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guest_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                capacity INTEGER NOT NULL DEFAULT 8,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guest_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(category, name)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guest_preference_rel (
                guest_id INTEGER NOT NULL,
                preference_id INTEGER NOT NULL,
                PRIMARY KEY (guest_id, preference_id),
                FOREIGN KEY (guest_id)
                    REFERENCES guests(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (preference_id)
                    REFERENCES guest_preferences(id)
                    ON DELETE CASCADE
            )
            """
        )

        default_preferences = (
            ("Étrend", "Vegetáriánus"),
            ("Étrend", "Vegán"),
            ("Érzékenység", "Gluténérzékeny"),
            ("Érzékenység", "Laktózérzékeny"),
            ("Érzékenység", "Tejérzékeny"),
            ("Allergia", "Diófélék"),
            ("Allergia", "Mogyoró"),
        )

        connection.executemany(
            """
            INSERT OR IGNORE INTO guest_preferences(
                category,
                name
            )
            VALUES (?, ?)
            """,
            default_preferences,
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS invitation_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                group_type TEXT NOT NULL DEFAULT 'Egyéb',
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                invitation_sent_date TEXT,
                rsvp_due_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if not _column_exists(
            connection,
            "invitation_groups",
            "contact_guest_id",
        ):
            connection.execute(
                """
                ALTER TABLE invitation_groups
                ADD COLUMN contact_guest_id INTEGER
                """
            )


        table_columns = {
            "position_x": "REAL NOT NULL DEFAULT 40",
            "position_y": "REAL NOT NULL DEFAULT 40",
            "shape": "TEXT NOT NULL DEFAULT 'Kerek'",
        }
        for column, column_type in table_columns.items():
            if not _column_exists(
                connection,
                "guest_tables",
                column,
            ):
                connection.execute(
                    f"""
                    ALTER TABLE guest_tables
                    ADD COLUMN {column} {column_type}
                    """
                )

        guest_seating_columns = {
            "seating_notes": "TEXT",
            "accessibility_required": "INTEGER NOT NULL DEFAULT 0",
        }
        for column, column_type in guest_seating_columns.items():
            if not _column_exists(
                connection,
                "guests",
                column,
            ):
                connection.execute(
                    f"""
                    ALTER TABLE guests
                    ADD COLUMN {column} {column_type}
                    """
                )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guest_seating_preferences (
                guest_id INTEGER NOT NULL,
                related_guest_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                PRIMARY KEY (
                    guest_id,
                    related_guest_id,
                    relation_type
                ),
                FOREIGN KEY (guest_id)
                    REFERENCES guests(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (related_guest_id)
                    REFERENCES guests(id)
                    ON DELETE CASCADE
            )
            """
        )
        connection.commit()
