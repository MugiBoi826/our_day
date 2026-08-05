from pathlib import Path


def test_generated_artifacts_are_not_in_repository():
    root = Path(__file__).parents[1]
    assert not (root / "build").exists()
    assert not (root / "dist").exists()
    assert not list((root / "src").rglob("__pycache__"))
