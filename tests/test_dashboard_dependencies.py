from pathlib import Path
import ast


def test_dashboard_exposes_quick_action_signals() -> None:
    source_path = (
        Path(__file__).parents[1]
        / "src"
        / "our_day"
        / "ui"
        / "pages"
        / "dashboard_page.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    dashboard_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "DashboardPage"
    )

    assigned_names = {
        target.id
        for node in dashboard_class.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    expected = {
        "create_service_requested",
        "create_task_requested",
        "create_guest_requested",
        "create_group_requested",
        "export_guests_requested",
        "backup_requested",
        "open_page_requested",
    }

    assert expected.issubset(assigned_names)
