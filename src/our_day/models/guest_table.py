from dataclasses import dataclass


@dataclass(slots=True)
class GuestTable:
    id: int | None
    name: str
    capacity: int = 8
    notes: str = ""
