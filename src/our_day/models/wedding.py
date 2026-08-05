from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Wedding:
    id: int | None = None
    bride_name: str = ""
    groom_name: str = ""
    wedding_date: date | None = None
    venue_name: str = ""
    venue_address: str = ""
    budget_amount: float = 0.0
    notes: str = ""
    is_active: bool = True

    @property
    def couple_name(self) -> str:
        names = [
            name.strip()
            for name in (self.bride_name, self.groom_name)
            if name.strip()
        ]
        return " & ".join(names)
