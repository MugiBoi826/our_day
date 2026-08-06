from dataclasses import dataclass, field


@dataclass(slots=True)
class Guest:
    id: int | None
    name: str
    email: str = ""
    phone: str = ""
    guest_type: str = "Felnőtt"
    invitation_status: str = "Tervezett"
    attendance_status: str = "Válaszra vár"
    has_plus_one: bool = False
    plus_one_name: str = ""
    attends_dinner: bool = True
    dietary_notes: str = ""
    table_name: str = ""
    table_id: int | None = None
    parent_guest_id: int | None = None
    family_group_id: int | None = None
    family_name: str = ""
    notes: str = ""
    invitation_group_id: int | None = None
    response_date: object | None = None
    is_contact_person: bool = False
    preference_ids: list[int] = field(default_factory=list)
    seating_notes: str = ""
    accessibility_required: bool = False

    @property
    def planned_headcount(self) -> int:
        return 1

    @property
    def confirmed_headcount(self) -> int:
        return 1 if self.attendance_status == "Részt vesz" else 0

    @property
    def waiting_headcount(self) -> int:
        return 1 if self.attendance_status == "Válaszra vár" else 0

    @property
    def declined_headcount(self) -> int:
        return 1 if self.attendance_status == "Nem vesz részt" else 0
