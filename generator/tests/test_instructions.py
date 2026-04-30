"""Tests for the post-generation Rich panel — focused on the conditional GCP IAM hint."""
from csfle_gen.instructions import _gcp_iam_hint
from csfle_gen.models import GenerationConfig, KafkaConfig, SrConfig


def _make_config(kms: str, kms_params: dict[str, str | None]) -> GenerationConfig:
    return GenerationConfig(
        project_name="demo",
        language="java",
        target="platform",
        kms=kms,
        kafka=KafkaConfig(bootstrap_servers="localhost:9091"),
        schema_registry=SrConfig(url="http://localhost:8081"),
        kms_params=kms_params,
        uid="9999",
    )


def test_hint_is_none_for_non_gcp() -> None:
    cfg = _make_config("aws", {"kms_key_id": "arn:aws:kms:..."})
    assert _gcp_iam_hint(cfg) is None


def test_hint_substitutes_parsed_key_path_and_email() -> None:
    cfg = _make_config(
        "gcp",
        {
            "kms_key_id": "projects/my-proj/locations/europe-west3/keyRings/my-ring/cryptoKeys/my-key",
            "client_email": "demo-sa@my-proj.iam.gserviceaccount.com",
        },
    )
    hint = _gcp_iam_hint(cfg)
    assert hint is not None
    assert "[dim]" in hint and "[/dim]" in hint
    assert "gcloud kms keys add-iam-policy-binding my-key" in hint
    assert "--keyring=my-ring" in hint
    assert "--location=europe-west3" in hint
    assert "--project=my-proj" in hint
    assert 'serviceAccount:demo-sa@my-proj.iam.gserviceaccount.com' in hint
    assert "roles/cloudkms.cryptoKeyEncrypterDecrypter" in hint


def test_hint_uses_placeholders_when_values_missing() -> None:
    cfg = _make_config("gcp", {"kms_key_id": None, "client_email": None})
    hint = _gcp_iam_hint(cfg)
    assert hint is not None
    for placeholder in ["<project>", "<location>", "<keyring>", "<key>", "<service-account-email>"]:
        assert placeholder in hint


def test_hint_uses_placeholders_when_key_path_malformed() -> None:
    cfg = _make_config(
        "gcp",
        {"kms_key_id": "not-a-valid-gcp-resource", "client_email": "demo@example.com"},
    )
    hint = _gcp_iam_hint(cfg)
    assert hint is not None
    assert "<project>" in hint and "<key>" in hint
    # Email is provided so it should be filled in even though the key path didn't parse.
    assert "demo@example.com" in hint
