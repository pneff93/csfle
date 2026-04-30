"""Tests for GCP service-account credential wiring in the generator output.

Two concerns are pinned down here:

1. The generated producer + consumer (both Python and Java) must pass the four
   GCP SA fields as `rule.executors._default_.param.*`. Without them the
   confluent_kafka GCP driver silently falls back to Application Default
   Credentials, masking IAM-permission misconfiguration.

2. For Java specifically, the `Config.getGcpPrivateKey()` getter must convert
   literal `\\n` escapes (as a key copied from a service-account JSON would
   contain) into real newline characters, since `dotenv-java` does not.
   This is verified by compiling the generated project and running a probe.

The Java probe test is skipped when Maven isn't installed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from csfle_gen.renderer import render
from tests.conftest import load_fixture

MVN = shutil.which("mvn")

# A fake PEM that contains the same escape pattern a real service-account key
# would have when copied verbatim from a JSON file (literal backslash + n).
LITERAL_BACKSLASH_N = "\\n"
TEST_KEY_LITERAL_N = (
    f"-----BEGIN PRIVATE KEY-----{LITERAL_BACKSLASH_N}"
    f"AAAA{LITERAL_BACKSLASH_N}BBBB{LITERAL_BACKSLASH_N}"
    f"-----END PRIVATE KEY-----{LITERAL_BACKSLASH_N}"
)

PROBE_SOURCE = r'''
package com.example.app;

public class KeyParsingProbe {
    public static void main(String[] args) {
        String key = Config.getGcpPrivateKey();
        if (key.contains("\\n")) {
            System.err.println("FAIL: literal '\\n' (backslash+n) still present in key");
            System.err.println("got=" + key);
            System.exit(1);
        }
        if (!key.contains("\n")) {
            System.err.println("FAIL: no real newlines in key after parsing");
            System.err.println("got=" + key);
            System.exit(2);
        }
        if (!key.startsWith("-----BEGIN PRIVATE KEY-----\n")) {
            System.err.println("FAIL: PEM header not separated by newline");
            System.err.println("got=" + key);
            System.exit(3);
        }
        System.out.println("OK");
    }
}
'''

# Required rule-executor param keys per KMS, per the canonical Kotlin examples in this repo.
# These are what the Confluent rule executors look up from the ser/deser conf — if any
# expected key is missing the executor silently falls back to its KMS-specific default
# (e.g. ADC for GCP), so we want to assert the generator emits all of them.
EXPECTED_GCP_PARAMS = [
    ("rule.executors._default_.param.client.id", "Config.getGcpClientId()"),
    ("rule.executors._default_.param.client.email", "Config.getGcpClientEmail()"),
    ("rule.executors._default_.param.private.key.id", "Config.getGcpPrivateKeyId()"),
    ("rule.executors._default_.param.private.key", "Config.getGcpPrivateKey()"),
]


def _replace_env_var(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text().splitlines()
    out = [f"{key}={value}" if line.startswith(f"{key}=") else line for line in lines]
    env_path.write_text("\n".join(out) + "\n")


def _run_probe(tmp_path: Path, env_value: str) -> subprocess.CompletedProcess:
    config = load_fixture("java-platform-gcp")
    render(config, tmp_path)
    _replace_env_var(tmp_path / ".env", "GCP_PRIVATE_KEY", env_value)
    probe = tmp_path / "src" / "main" / "java" / "com" / "example" / "app" / "KeyParsingProbe.java"
    probe.write_text(PROBE_SOURCE)
    return subprocess.run(
        [MVN, "-q", "compile", "exec:java", "-Dexec.mainClass=com.example.app.KeyParsingProbe"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=600,
    )


@pytest.mark.skipif(MVN is None, reason="Maven not available; skipping Java integration test")
def test_gcp_private_key_unquoted_with_literal_backslash_n(tmp_path: Path) -> None:
    """User pasted the SA-JSON value WITHOUT surrounding double quotes."""
    result = _run_probe(tmp_path, TEST_KEY_LITERAL_N)
    assert result.returncode == 0 and "OK" in result.stdout, (
        f"Probe failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.skipif(MVN is None, reason="Maven not available; skipping Java integration test")
def test_gcp_private_key_quoted_with_literal_backslash_n(tmp_path: Path) -> None:
    """User pasted the SA-JSON value WITH surrounding double quotes (per the wizard hint)."""
    result = _run_probe(tmp_path, f'"{TEST_KEY_LITERAL_N}"')
    assert result.returncode == 0 and "OK" in result.stdout, (
        f"Probe failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.parametrize("source_file", ["BasicProducer.java", "BasicConsumer.java"])
def test_java_gcp_passes_service_account_to_rule_executor(tmp_path: Path, source_file: str) -> None:
    """The generated Java producer/consumer must wire all four GCP SA fields into the rule executor.

    If any of these is missing, the Java rule executor silently falls back to ADC
    (Application Default Credentials) and authenticates as whatever identity the local
    machine has — masking IAM-permission bugs and producing confusing failures.
    """
    config = load_fixture("java-platform-gcp")
    render(config, tmp_path)
    src = (tmp_path / "src" / "main" / "java" / "com" / "example" / "app" / source_file).read_text()
    missing = [
        f'props.setProperty("{key}", {getter})'
        for key, getter in EXPECTED_GCP_PARAMS
        if f'"{key}"' not in src or getter not in src
    ]
    assert not missing, f"{source_file} missing rule.executors lines:\n  " + "\n  ".join(missing)


# Python rule_conf keys are UNPREFIXED — confluent_kafka's AvroSerializer passes the
# rule_conf dict verbatim to the KMS driver, which calls `conf.get('client.id')`. The
# `rule.executors._default_.param.` prefix that Java/Kotlin Properties use is stripped
# by the JVM Kafka client config layer, but the Python serializer has no such layer.
# If we used the prefixed keys here the GCP driver would see all four params as None
# and fall back to Application Default Credentials.
EXPECTED_PYTHON_GCP_PARAMS = [
    ("client.id", "os.getenv('GCP_CLIENT_ID')"),
    ("client.email", "os.getenv('GCP_CLIENT_EMAIL')"),
    ("private.key.id", "os.getenv('GCP_PRIVATE_KEY_ID')"),
    ("private.key", "os.getenv('GCP_PRIVATE_KEY')"),
]


def test_python_rule_conf_keys_are_unprefixed_so_gcp_driver_actually_sees_them() -> None:
    """Regression guard: Python rule_conf keys must NOT use the `rule.executors._default_.param.`
    prefix that Java uses. The Python AvroSerializer hands rule_conf verbatim to the KMS driver;
    if the prefix is present, the driver's `conf.get('client.id')` returns None and the GCP
    driver silently falls back to Application Default Credentials.

    This was the exact bug behind one round of debugging: prefixed keys made Python "appear to
    work" via ADC fallback while Java (which uses the same prefixed keys but its Properties layer
    strips them) actually authenticated as the SA from .env and surfaced the real IAM error.

    The upstream constants are read from the gcp_driver.py source file as text rather than
    imported, so this works in any environment that has the confluent_kafka package installed
    (even without optional schemaregistry/httpx deps).
    """
    import importlib.util

    spec = importlib.util.find_spec("confluent_kafka")
    if spec is None or spec.origin is None:
        pytest.skip("confluent_kafka not installed")
    pkg_root = Path(spec.origin).parent
    driver_src = pkg_root / "schema_registry" / "rules" / "encryption" / "gcpkms" / "gcp_driver.py"
    if not driver_src.is_file():
        pytest.skip(f"gcp_driver.py not found at {driver_src}")

    text = driver_src.read_text()

    upstream_keys = set(re.findall(r'^_(?:CLIENT_ID|CLIENT_EMAIL|PRIVATE_KEY_ID|PRIVATE_KEY)\s*=\s*"([^"]+)"', text, re.M))
    assert upstream_keys == {"client.id", "client.email", "private.key.id", "private.key"}, (
        f"Upstream gcp_driver renamed its conf keys; update the Python kms_gcp.j2 partial. "
        f"Got {upstream_keys}"
    )


@pytest.mark.parametrize("source_file", ["avro_producer.py", "avro_consumer.py"])
def test_python_gcp_passes_service_account_to_rule_executor(tmp_path: Path, source_file: str) -> None:
    """The generated Python producer/consumer must wire all four GCP SA fields too.

    Without them the Python GCP driver returns `creds=None` and google-auth walks its
    ADC chain — authenticating as the local `gcloud` user rather than the SA from .env.
    This was the latent bug that made the Python flow appear to "work" while the Java
    flow (which correctly uses the SA) failed with 403 IAM_PERMISSION_DENIED.

    The params must be passed via the `rule_conf=` kwarg of AvroSerializer/AvroDeserializer.
    Putting them in the regular `conf=` dict raises `ValueError: Unrecognized properties`.
    """
    config = load_fixture("python-platform-gcp")
    render(config, tmp_path)
    src = (tmp_path / source_file).read_text()
    missing = [
        f"'{key}': {value}"
        for key, value in EXPECTED_PYTHON_GCP_PARAMS
        if f"'{key}'" not in src or value not in src
    ]
    assert not missing, f"{source_file} missing rule.executors lines:\n  " + "\n  ".join(missing)
    assert "rule_conf=rule_conf" in src, (
        f"{source_file} doesn't pass rule_conf= kwarg to the (de)serializer; the "
        f"AvroSerializer/AvroDeserializer rejects rule.executors keys in the regular conf dict."
    )
