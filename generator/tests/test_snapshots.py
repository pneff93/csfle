"""Snapshot tests: render every fixture, compare file-by-file against frozen output."""
import shutil
from pathlib import Path

import pytest

from csfle_gen.renderer import render
from tests.conftest import FIXTURES_DIR, SNAPSHOTS_DIR, load_fixture

def _combos() -> list[str]:
    return sorted(p.stem for p in FIXTURES_DIR.glob("*.yaml"))


@pytest.fixture
def update_snapshots(request) -> bool:
    return request.config.getoption("--snapshot-update")


@pytest.mark.parametrize("combo", _combos())
def test_snapshot_matches(combo: str, tmp_path: Path, update_snapshots: bool) -> None:
    config = load_fixture(combo)
    render(config, tmp_path)

    expected_dir = SNAPSHOTS_DIR / config.language / combo

    if update_snapshots:
        if expected_dir.exists():
            shutil.rmtree(expected_dir)
        shutil.copytree(tmp_path, expected_dir)
        return

    assert expected_dir.is_dir(), (
        f"No snapshot at {expected_dir}. Run `pytest --snapshot-update` to create it."
    )

    actual_files = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    expected_files = {p.relative_to(expected_dir) for p in expected_dir.rglob("*") if p.is_file()}

    assert actual_files == expected_files, (
        f"File set mismatch for {combo}:\n"
        f"  only in actual:   {sorted(actual_files - expected_files)}\n"
        f"  only in expected: {sorted(expected_files - actual_files)}"
    )

    for rel in sorted(actual_files):
        actual = (tmp_path / rel).read_text()
        expected = (expected_dir / rel).read_text()
        assert actual == expected, f"{combo}/{rel} differs from snapshot"
