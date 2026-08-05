from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "our_day.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row["name"] == column for row in connection.execute(f"PRAGMA table_info({table})"))


def initialize_database() -> None:
    with get_connection() as connection:
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
        for name in ("deposit_due_date", "deposit_paid_date", "payment_due_date"):
            if not _column_exists(connection, "entries", name):
                connection.execute(f"ALTER TABLE entries ADD COLUMN {name} TEXT")

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

        if not _column_exists(connection, "guests", "table_id"):
            connection.execute("ALTER TABLE guests ADD COLUMN table_id INTEGER")
        if not _column_exists(connection, "guests", "parent_guest_id"):
            connection.execute("ALTER TABLE guests ADD COLUMN parent_guest_id INTEGER")

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

        if not _column_exists(connection, "guests", "family_group_id"):
            connection.execute(
                "ALTER TABLE guests ADD COLUMN family_group_id INTEGER"
            )
        if not _column_exists(connection, "guests", "family_name"):
            connection.execute(
                "ALTER TABLE guests ADD COLUMN family_name TEXT"
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
                FOREIGN KEY (guest_id) REFERENCES guests(id) ON DELETE CASCADE,
                FOREIGN KEY (preference_id)
                    REFERENCES guest_preferences(id) ON DELETE CASCADE
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
            INSERT OR IGNORE INTO guest_preferences(category, name)
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

        if not _column_exists(connection, "guests", "invitation_group_id"):
            connection.execute(
                "ALTER TABLE guests ADD COLUMN invitation_group_id INTEGER"
            )
        if not _column_exists(connection, "guests", "response_date"):
            connection.execute(
                "ALTER TABLE guests ADD COLUMN response_date TEXT"
            )
        if not _column_exists(connection, "guests", "is_contact_person"):
            connection.execute(
                "ALTER TABLE guests ADD COLUMN is_contact_person INTEGER NOT NULL DEFAULT 0"
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
        connection.commit()
