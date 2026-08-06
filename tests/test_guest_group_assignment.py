from pathlib import Path
from our_day.database import connection as database_connection
from our_day.models.guest import Guest
from our_day.models.invitation_group import InvitationGroup
from our_day.repositories.guest_repository import GuestRepository
from our_day.repositories.invitation_group_repository import InvitationGroupRepository


def test_assign_existing_guest_to_group(tmp_path: Path) -> None:
    database_connection.DATA_DIR = tmp_path
    database_connection.DATABASE_PATH = tmp_path / "our_day.db"
    database_connection.initialize_database()
    guests = GuestRepository()
    groups = InvitationGroupRepository()
    guest_id = guests.create(Guest(id=None, name="Teszt Vendég"))
    group_id = groups.create(InvitationGroup(id=None, name="Teszt Csoport"))
    guests.assign_guests_to_group([guest_id], group_id)
    guest = guests.get_by_id(guest_id)
    assert guest is not None
    assert guest.invitation_group_id == group_id
