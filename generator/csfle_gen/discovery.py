"""Load wizard defaults from the canonical generator/.env file.

Angle-bracket placeholder values (e.g. `<AWS KMS Key ARN>`) are filtered out so
the wizard doesn't show them as defaults — they're "fill this in" markers, not
usable values.
"""
from pathlib import Path

from dotenv import dotenv_values


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("<") and stripped.endswith(">")


def discover_defaults(env_path: Path) -> dict[str, str]:
    """Return env-var → value mapping from `env_path`, or empty if it doesn't exist."""
    if not env_path.is_file():
        return {}
    raw = dotenv_values(env_path)
    return {k: v for k, v in raw.items() if v and not _is_placeholder(v)}
