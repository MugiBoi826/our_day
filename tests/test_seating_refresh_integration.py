from pathlib import Path
import ast


def test_main_window_refreshes_seating_page() -> None:
    path = (
        Path(__file__).parents[1]
        / "src"
        / "our_day"
        / "ui"
        / "main_window.py"
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    main_window = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "MainWindow"
    )
    refresh_method = next(
        node
        for node in main_window.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_refresh"
    )

    calls = {
        ast.unparse(node.func)
        for node in ast.walk(refresh_method)
        if isinstance(node, ast.Call)
    }

    assert "self.seating.refresh" in calls


def test_seating_page_initializes_runtime_state() -> None:
    path = (
        Path(__file__).parents[1]
        / "src"
        / "our_day"
        / "ui"
        / "pages"
        / "seating_page.py"
    )
    source = path.read_text(encoding="utf-8")

    assert "self.guests = []" in source
    assert "self.tables = []" in source
    assert "self.preference_map = {}" in source
    table_item_path = (
        Path(__file__).parents[1]
        / "src"
        / "our_day"
        / "ui"
        / "seating"
        / "table_item.py"
    )
    table_item_source = table_item_path.read_text(encoding="utf-8")
    assert "class MovableTableItem(QGraphicsObject)" in table_item_source
