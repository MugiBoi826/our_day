from dataclasses import dataclass


@dataclass(slots=True)
class GuestTable:
    id: int | None
    name: str
    capacity: int = 8
    notes: str = ""
    position_x: float = 40
    position_y: float = 40
    shape: str = "Kerek"
