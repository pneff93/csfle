"""Scan the repo for existing .env / .env.example files matching a (target, kms) combo
and return their values to be used as wizard prompt defaults.

The values are filtered to drop angle-bracket placeholders (e.g. `<AWS KMS Key ARN>`),
since those represent "fill this in" markers rather than usable defaults.
"""
from pathlib import Path

from dotenv import dotenv_values

from csfle_gen.models import Kms, Target


def _candidate_paths(target: Target, kms: Kms, repo_root: Path) -> list[Path]:
    if target == "platform":
        base = repo_root / "confluent_platform" / kms
    else:
        base = repo_root / "confluent_cloud" / kms / "python"
    return [base / ".env", base / ".env.example"]


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("<") and stripped.endswith(">")


def discover_defaults(target: Target, kms: Kms, repo_root: Path) -> dict[str, str]:
    """Return env-var → value mapping from the first existing canonical .env file.

    Returns an empty dict if no candidate file exists. Placeholder-style values
    (`<...>`) are excluded so the wizard doesn't show them as defaults.
    """
    for path in _candidate_paths(target, kms, repo_root):
        if not path.is_file():
            continue
        raw = dotenv_values(path)
        return {k: v for k, v in raw.items() if v and not _is_placeholder(v)}
    return {}
