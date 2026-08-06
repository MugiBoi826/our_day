from pathlib import Path

from our_day.database import connection as database_connection
from our_day.models.entry import Entry
from our_day.repositories.entry_repository import EntryRepository


def _entry(title: str, status: str, deposit: float, total: float) -> Entry:
    return Entry(
        id=None,
        entry_type="Szolgáltatás",
        title=title,
        deposit_amount=deposit,
        total_amount=total,
        status=status,
    )


def test_financial_summary_starts_from_booked_status(tmp_path: Path) -> None:
    database_connection.DATA_DIR = tmp_path
    database_connection.DATABASE_PATH = tmp_path / "our_day.db"
    database_connection.initialize_database()

    repository = EntryRepository()

    repository.create(
        _entry("Ötlet", "Ötlet", 20_000, 100_000)
    )
    repository.create(
        _entry("Ajánlat", "Ajánlatkérés", 30_000, 150_000)
    )
    repository.create(
        _entry("Foglalva", "Lefoglalva", 40_000, 200_000)
    )
    repository.create(
        _entry("Részben fizetve", "Részben fizetve", 50_000, 250_000)
    )
    repository.create(
        _entry("Kifizetve", "Kifizetve", 60_000, 300_000)
    )
    repository.create(
        _entry("Lemondva", "Lemondva", 70_000, 350_000)
    )

    summary = repository.get_financial_summary("Szolgáltatás")

    assert summary["total"] == 750_000
    assert summary["deposits"] == 90_000
    assert summary["paid"] == 350_000
    assert summary["remaining"] == 360_000
