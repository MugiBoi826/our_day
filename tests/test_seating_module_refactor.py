from pathlib import Path
import ast


def test_seating_modules_have_valid_import_locations() -> None:
    root = Path(__file__).parents[1]

    room_export = (
        root
        / "src"
        / "our_day"
        / "ui"
        / "seating"
        / "room_export.py"
    ).read_text(encoding="utf-8")

    assert (
        "from PySide6.QtCore import"
        in room_export
    )
    assert "QPageSize" in room_export
    assert (
        "from PySide6.QtGui import"
        in room_export
    )
    assert "QPageLayout" in room_export
    assert (
        "from PySide6.QtPrintSupport import"
        in room_export
    )
    assert "QPrinter" in room_export
    assert "QPrintDialog" in room_export


def test_seating_page_is_split_into_components() -> None:
    root = Path(__file__).parents[1]
    package = (
        root
        / "src"
        / "our_day"
        / "ui"
        / "seating"
    )

    expected = {
        "drag_list.py",
        "table_item.py",
        "room_export.py",
        "auto_seating.py",
    }

    assert expected.issubset(
        {
            path.name
            for path in package.iterdir()
            if path.is_file()
        }
    )


def test_refactored_files_parse() -> None:
    root = Path(__file__).parents[1]

    files = (
        root
        / "src"
        / "our_day"
        / "ui"
        / "pages"
        / "seating_page.py",
        root
        / "src"
        / "our_day"
        / "ui"
        / "seating"
        / "drag_list.py",
        root
        / "src"
        / "our_day"
        / "ui"
        / "seating"
        / "table_item.py",
        root
        / "src"
        / "our_day"
        / "ui"
        / "seating"
        / "room_export.py",
        root
        / "src"
        / "our_day"
        / "ui"
        / "seating"
        / "auto_seating.py",
    )

    for path in files:
        ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )
