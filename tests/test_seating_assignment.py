from pathlib import Path

from our_day.database import connection as database_connection
from our_day.models.guest import Guest
from our_day.models.guest_table import GuestTable
from our_day.repositories.guest_repository import GuestRepository
from our_day.repositories.guest_table_repository import (
    GuestTableRepository,
)


def test_guest_can_be_assigned_and_unassigned_from_table(
    tmp_path: Path,
) -> None:
    database_connection.DATA_DIR = tmp_path
    database_connection.DATABASE_PATH = (
        tmp_path / "our_day.db"
    )
    database_connection.initialize_database()

    guest_repository = GuestRepository()
    table_repository = GuestTableRepository()

    table_id = table_repository.create(
        GuestTable(
            id=None,
            name="Teszt asztal",
            capacity=8,
        )
    )

    guest_id = guest_repository.create(
        Guest(
            id=None,
            name="Teszt Vendég",
            attendance_status="Részt vesz",
        )
    )

    guest_repository.assign_guests_to_table(
        [guest_id],
        table_id,
    )

    assigned_guest = guest_repository.get_by_id(
        guest_id
    )

    assert assigned_guest is not None
    assert assigned_guest.table_id == table_id
    assert assigned_guest.table_name == "Teszt asztal"

    guest_repository.assign_guests_to_table(
        [guest_id],
        None,
    )

    unassigned_guest = guest_repository.get_by_id(
        guest_id
    )

    assert unassigned_guest is not None
    assert unassigned_guest.table_id is None
    assert unassigned_guest.table_name == ""
