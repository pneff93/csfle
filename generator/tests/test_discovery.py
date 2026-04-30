from pathlib import Path

from csfle_gen.discovery import discover_defaults


def test_returns_empty_when_no_file(tmp_path: Path) -> None:
    assert discover_defaults("platform", "aws", tmp_path) == {}


def test_loads_platform_env(tmp_path: Path) -> None:
    target_dir = tmp_path / "confluent_platform" / "aws"
    target_dir.mkdir(parents=True)
    (target_dir / ".env").write_text(
        "KAFKA_BOOTSTRAP_SERVERS=localhost:9091\n"
        "AWS_KMS_KEY_ID=arn:aws:kms:us-east-1:123:key/abc\n"
    )
    result = discover_defaults("platform", "aws", tmp_path)
    assert result["KAFKA_BOOTSTRAP_SERVERS"] == "localhost:9091"
    assert result["AWS_KMS_KEY_ID"] == "arn:aws:kms:us-east-1:123:key/abc"


def test_falls_back_to_env_example(tmp_path: Path) -> None:
    target_dir = tmp_path / "confluent_platform" / "aws"
    target_dir.mkdir(parents=True)
    (target_dir / ".env.example").write_text("KAFKA_BOOTSTRAP_SERVERS=localhost:9091\n")
    result = discover_defaults("platform", "aws", tmp_path)
    assert result["KAFKA_BOOTSTRAP_SERVERS"] == "localhost:9091"


def test_filters_angle_bracket_placeholders(tmp_path: Path) -> None:
    target_dir = tmp_path / "confluent_platform" / "aws"
    target_dir.mkdir(parents=True)
    (target_dir / ".env").write_text(
        "KAFKA_BOOTSTRAP_SERVERS=localhost:9091\n"
        "AWS_KMS_KEY_ID=<AWS KMS Key ARN>\n"
        "AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>\n"
    )
    result = discover_defaults("platform", "aws", tmp_path)
    assert result == {"KAFKA_BOOTSTRAP_SERVERS": "localhost:9091"}


def test_cloud_uses_python_subdirectory(tmp_path: Path) -> None:
    target_dir = tmp_path / "confluent_cloud" / "azure" / "python"
    target_dir.mkdir(parents=True)
    (target_dir / ".env").write_text("AZURE_TENANT_ID=00000000-0000-0000-0000-000000000000\n")
    result = discover_defaults("cloud", "azure", tmp_path)
    assert result["AZURE_TENANT_ID"] == "00000000-0000-0000-0000-000000000000"
