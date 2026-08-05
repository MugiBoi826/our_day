from datetime import date

from our_day.models.wedding import Wedding
from our_day.repositories.wedding_repository import WeddingRepository


def test_wedding_model_couple_name():
    wedding = Wedding(bride_name="Anna", groom_name="Péter")
    assert wedding.couple_name == "Anna & Péter"


def test_wedding_model_handles_missing_name():
    wedding = Wedding(bride_name="Anna", wedding_date=date(2027, 5, 22))
    assert wedding.couple_name == "Anna"
