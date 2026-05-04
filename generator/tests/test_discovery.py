from pathlib import Path

from csfle_gen.discovery import discover_defaults


def test_returns_empty_when_missing_file(tmp_path: Path) -> None:
    assert discover_defaults(tmp_path / "nope.env") == {}


def test_loads_env(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "KAFKA_BOOTSTRAP_SERVERS=localhost:9091\n"
        "AWS_KMS_KEY_ID=arn:aws:kms:us-east-1:123:key/abc\n"
    )
    result = discover_defaults(env)
    assert result["KAFKA_BOOTSTRAP_SERVERS"] == "localhost:9091"
    assert result["AWS_KMS_KEY_ID"] == "arn:aws:kms:us-east-1:123:key/abc"


def test_filters_angle_bracket_placeholders(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "KAFKA_BOOTSTRAP_SERVERS=localhost:9091\n"
        "AWS_KMS_KEY_ID=<AWS KMS Key ARN>\n"
        "AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>\n"
    )
    assert discover_defaults(env) == {"KAFKA_BOOTSTRAP_SERVERS": "localhost:9091"}
