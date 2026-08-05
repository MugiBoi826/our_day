from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Task:
    id: int | None
    title: str
    description: str = ""
    due_date: date | None = None
    priority: str = "Közepes"
    status: str = "Teendő"
