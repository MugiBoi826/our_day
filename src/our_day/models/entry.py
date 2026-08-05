from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Entry:
    id: int | None
    entry_type: str
    title: str
    description: str = ""
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    deposit_amount: float = 0.0
    total_amount: float = 0.0
    status: str = "Ötlet"
    deposit_due_date: date | None = None
    deposit_paid_date: date | None = None
    payment_due_date: date | None = None

    @property
    def remaining_amount(self) -> float:
        if self.status in ("Kifizetve", "Lemondva"):
            return 0.0
        return max(self.total_amount - self.deposit_amount, 0.0)
