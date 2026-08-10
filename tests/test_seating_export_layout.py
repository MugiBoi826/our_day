from pathlib import Path


def test_seating_export_has_distinct_sheets() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "our_day"
        / "services"
        / "seating_export_service.py"
    ).read_text(encoding="utf-8")

    assert 'add_worksheet("Asztalok")' in source
    assert 'add_worksheet("Catering")' in source
    assert 'add_worksheet(' in source
    assert '"Étrend összesítő"' in source
    assert '"Asztal nélkül"' in source
    assert "Catering összesítő asztalonként" in source
