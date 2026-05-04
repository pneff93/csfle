from pathlib import Path

import pytest
import yaml

from csfle_gen.models import GenerationConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def pytest_addoption(parser):
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Overwrite snapshot directories with the freshly rendered output.",
    )


def load_fixture(name: str) -> GenerationConfig:
    """Load a YAML fixture under tests/fixtures/ and build a GenerationConfig."""
    path = FIXTURES_DIR / f"{name}.yaml"
    data = yaml.safe_load(path.read_text())
    return GenerationConfig(**data)


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def snapshots_dir() -> Path:
    return SNAPSHOTS_DIR
