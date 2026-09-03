from pathlib import Path
import sqlite3

from our_day.database import connection as database_connection
from our_day.services.supabase_sync_service import SupabaseSyncService


class FixtureSync(SupabaseSyncService):
    def __init__(self) -> None:
        super().__init__()
        self.access_token = "test-token"
        self.wedding_id = "wedding-1"

    def _get_one(self, table: str, query: str):
        return {
            "bride_name": "Johanna", "groom_name": "Feli",
            "wedding_date": "2027-05-22", "venue_name": "Ligeti ház",
            "venue_address": "Budapest", "budget_amount": 5000000,
            "notes": "Teszt", "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-09-03T00:00:00Z",
        }

    def _get_all(self, table: str, wedding_id: str):
        fixtures = {
            "guest_tables": [{"id": "table-1", "legacy_id": 4, "name": "Család",
                              "capacity": 8, "shape": "Kerek"}],
            "invitation_groups": [{"id": "group-1", "legacy_id": 3,
                                   "name": "Kovács család", "group_type": "Család"}],
            "guest_preferences": [{"id": "pref-1", "legacy_id": 2,
                                   "category": "Étrend", "name": "Vegán"}],
            "guests": [{"id": "guest-1", "legacy_id": 7, "name": "Teszt Elek",
                        "table_id": "table-1", "invitation_group_id": "group-1",
                        "attends_dinner": True}],
            "tasks": [{"id": "task-1", "legacy_id": 5, "title": "Próba",
                       "priority": "Közepes", "status": "Teendő"}],
            "entries": [{"id": "entry-1", "legacy_id": 6,
                         "entry_type": "Szolgáltatás", "title": "Fotós",
                         "deposit_amount": 0, "total_amount": 100000,
                         "status": "Ötlet"}],
        }
        return fixtures[table]

    def _get_relations(self, table: str, guest_ids: list[str]):
        if table == "guest_preference_rel":
            return [{"guest_id": "guest-1", "preference_id": "pref-1"}]
        return []


def test_cloud_download_rebuilds_sqlite_cache(tmp_path: Path) -> None:
    database_connection.DATA_DIR = tmp_path
    database_connection.DATABASE_PATH = tmp_path / "cache.db"
    database_connection.initialize_database()

    counts = FixtureSync().download_to_cache()

    assert counts == {"guests": 1, "tasks": 1, "entries": 1, "tables": 1, "groups": 1}
    with sqlite3.connect(database_connection.DATABASE_PATH) as connection:
        assert connection.execute("SELECT bride_name FROM weddings").fetchone()[0] == "Johanna"
        assert connection.execute("SELECT table_id FROM guests WHERE id=7").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM guest_preference_rel").fetchone()[0] == 1
