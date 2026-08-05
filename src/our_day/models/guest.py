from dataclasses import dataclass


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
    notes: str = ""

    @property
    def planned_headcount(self) -> int:
        return 1

    @property
    def confirmed_headcount(self) -> int:
        if self.attendance_status != "Részt vesz":
            return 0
        return 1

    @property
    def waiting_headcount(self) -> int:
        if self.attendance_status != "Válaszra vár":
            return 0
        return 1

    @property
    def declined_headcount(self) -> int:
        if self.attendance_status != "Nem vesz részt":
            return 0
        return 1
