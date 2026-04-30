from pathlib import Path

from csfle_gen.models import GenerationConfig, KafkaConfig, SrConfig
from csfle_gen.renderer import render


def _minimal_config() -> GenerationConfig:
    return GenerationConfig(
        project_name="test",
        target="platform",
        kms="aws",
        kafka=KafkaConfig(bootstrap_servers="localhost:9091"),
        schema_registry=SrConfig(url="http://localhost:8081"),
        kms_params={},
    )


def test_render_writes_avro_schema(tmp_path: Path) -> None:
    written = render(_minimal_config(), tmp_path)

    avsc = tmp_path / "avro" / "personal_data.avsc"
    assert avsc.exists()
    assert avsc in written

    content = avsc.read_text()
    assert '"PersonalData"' in content
    assert '"PII"' in content
    assert '"birthday"' in content
