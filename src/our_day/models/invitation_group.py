from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class InvitationGroup:
    id: int | None
    name: str
    group_type: str = "Egyéb"
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    invitation_sent_date: date | None = None
    rsvp_due_date: date | None = None
    notes: str = ""
    contact_guest_id: int | None = None
