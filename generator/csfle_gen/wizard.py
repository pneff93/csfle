"""Interactive wizard that produces a (GenerationConfig, output_dir) pair from prompts."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

import questionary
from rich.console import Console
from rich.table import Table

from csfle_gen.discovery import discover_defaults
from csfle_gen.models import GenerationConfig, KafkaConfig, Kms, Language, SrConfig, Target

PROJECT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")


class WizardCancelled(Exception):
    pass


@dataclass(frozen=True)
class _KmsField:
    config_key: str   # key under GenerationConfig.kms_params
    label: str        # prompt text shown to user
    env_var: str      # env-var name discovery looks up for the default
    secret: bool      # if True, use password() prompt; if blank → None → <FILL_ME>


_KMS_FIELDS: dict[Kms, list[_KmsField]] = {
    "aws": [
        _KmsField("kms_key_id", "AWS KMS Key ARN", "AWS_KMS_KEY_ID", False),
        _KmsField("access_key_id", "AWS Access Key ID", "AWS_ACCESS_KEY_ID", False),
        _KmsField("secret_access_key", "AWS Secret Access Key", "AWS_SECRET_ACCESS_KEY", True),
    ],
    "azure": [
        _KmsField("kms_key_id", "Azure Key Vault key URL", "AZURE_KMS_KEY_ID", False),
        _KmsField("tenant_id", "Azure Tenant ID", "AZURE_TENANT_ID", False),
        _KmsField("client_id", "Azure Client ID", "AZURE_CLIENT_ID", False),
        _KmsField("client_secret", "Azure Client Secret", "AZURE_CLIENT_SECRET", True),
    ],
    "gcp": [
        _KmsField(
            "kms_key_id",
            "GCP KMS key (projects/.../cryptoKeys/<key>) — DO NOT include /cryptoKeyVersions/N",
            "GCP_KMS_KEY_ID",
            False,
        ),
        _KmsField("client_id", "GCP service account client_id", "GCP_CLIENT_ID", False),
        _KmsField("client_email", "GCP service account client_email", "GCP_CLIENT_EMAIL", False),
        _KmsField("private_key_id", "GCP service account private_key_id", "GCP_PRIVATE_KEY_ID", False),
        _KmsField("private_key", "GCP service account private_key (paste with quotes)", "GCP_PRIVATE_KEY", True),
    ],
    "hashicorp": [
        _KmsField("kms_key_id", "Vault Transit KEK URL (e.g. http://127.0.0.1:8200/transit/keys/csfle)", "HCVAULT_KMS_KEY_ID", False),
        _KmsField("vault_addr", "Vault address (VAULT_ADDR)", "VAULT_ADDR", False),
        _KmsField("vault_token", "Vault token (VAULT_TOKEN)", "VAULT_TOKEN", True),
    ],
}

_KMS_LABELS = {
    "aws": "AWS KMS",
    "azure": "Azure Key Vault",
    "gcp": "Google Cloud KMS",
    "hashicorp": "HashiCorp Vault",
}


def _validate_project_name(value: str) -> bool | str:
    if PROJECT_NAME_RE.match(value.strip()):
        return True
    return "Use lowercase letters, digits, and dashes (start with a letter); max 64 chars."


def _ask_or_cancel(prompt) -> str:
    answer = prompt.ask()
    if answer is None:
        raise WizardCancelled()
    return answer


def _optional(value: str) -> str | None:
    """Empty string → None (becomes <FILL_ME> at render time)."""
    return value if value else None


def sanitize_gcp_private_key(raw: str) -> str:
    """Normalize a pasted GCP private_key value into a single-line `\\n`-escaped PEM.

    The user usually copy-pastes the private_key from the service-account JSON file.
    Common pasted forms — all of which we try to handle:
      1. The bare value with `\\n` escapes:  -----BEGIN PRIVATE KEY-----\\n…\\n-----END PRIVATE KEY-----\\n
      2. JSON-quoted:                        "-----BEGIN PRIVATE KEY-----\\n…\\n-----END PRIVATE KEY-----\\n"
      3. Over-pasted (case 2 + a trailing comma + the next JSON field):
                                             "-----BEGIN ...\\n",\\n  "client_email": "..."
      4. Multi-line raw PEM (real newlines).

    Cases 2 and 3 are detected by a leading `"` and resolved with `JSONDecoder.raw_decode`,
    which parses just the leading JSON string and discards anything after. The result is
    then re-encoded with literal `\\n` (so the rendered .env stays single-line).
    """
    value = raw.strip()
    if not value:
        return value

    if value.startswith('"'):
        try:
            decoded, _ = json.JSONDecoder().raw_decode(value)
            if isinstance(decoded, str):
                value = decoded
        except json.JSONDecodeError:
            # Not valid JSON; fall through and treat as a raw value.
            pass

    # Collapse any real newlines (CRLF or LF) the user may have pasted into the
    # `\n` literal escape that .env files expect for single-line values.
    value = value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "")

    # The outer .strip() above removed any trailing real newline that the user's
    # PEM canonically ended with. Restore it as a literal `\n` so the resulting
    # PEM is well-formed (`-----END PRIVATE KEY-----\n`).
    if "-----END" in value and not value.endswith("\\n"):
        value += "\\n"

    return value


def run_wizard(repo_root: Path) -> tuple[GenerationConfig, Path]:
    console = Console()

    console.rule("[bold]CSFLE client generator[/bold]")

    # Phase 1 — project basics
    project_name = _ask_or_cancel(
        questionary.text("Project name", validate=_validate_project_name)
    ).strip()
    description = _ask_or_cancel(questionary.text("Short description (optional)")).strip()

    # Phase 1b — client language
    language: Language = _ask_or_cancel(
        questionary.select(
            "Client language",
            choices=[
                questionary.Choice("Python", value="python"),
                questionary.Choice("Java (Maven)", value="java"),
            ],
        )
    )

    # Phase 2 — Confluent target
    target: Target = _ask_or_cancel(
        questionary.select(
            "Confluent target",
            choices=[
                questionary.Choice("Confluent Platform (local Docker)", value="platform"),
                questionary.Choice("Confluent Cloud", value="cloud"),
            ],
        )
    )

    # Phase 3 — KMS provider (chosen now so discovery can populate defaults)
    kms: Kms = _ask_or_cancel(
        questionary.select(
            "KMS provider",
            choices=[
                questionary.Choice(_KMS_LABELS[k], value=k) for k in _KMS_FIELDS
            ],
        )
    )

    defaults = discover_defaults(target, kms, repo_root)
    if defaults:
        console.print(
            f"[dim]Found existing config in the repo for {target}/{kms} — using its values as defaults.[/dim]"
        )

    # Phase 4 — Kafka + SR
    if target == "cloud":
        kafka = KafkaConfig(
            bootstrap_servers=_ask_or_cancel(
                questionary.text(
                    "Kafka bootstrap server",
                    default=defaults.get("KAFKA_BOOTSTRAP_SERVERS", ""),
                )
            ),
            sasl_username=_optional(_ask_or_cancel(
                questionary.text(
                    "Kafka API key (KAFKA_SASL_USERNAME) — Enter to skip",
                    default=defaults.get("KAFKA_SASL_USERNAME", ""),
                )
            )),
            sasl_password=_optional(_ask_or_cancel(
                questionary.password(
                    "Kafka API secret — Enter to skip",
                )
            )),
        )
        sr_url = _ask_or_cancel(
            questionary.text(
                "Schema Registry URL",
                default=defaults.get("SCHEMA_REGISTRY_URL", ""),
            )
        )
        sr_api_key = _ask_or_cancel(
            questionary.text("Schema Registry API key — Enter to skip")
        )
        sr_api_secret = _ask_or_cancel(
            questionary.password("Schema Registry API secret — Enter to skip")
        )
        sr_auth = f"{sr_api_key}:{sr_api_secret}" if sr_api_key and sr_api_secret else None
        sr = SrConfig(url=sr_url, basic_auth_user_info=sr_auth)
    else:
        kafka = KafkaConfig(
            bootstrap_servers=_ask_or_cancel(
                questionary.text(
                    "Kafka bootstrap server",
                    default=defaults.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9091"),
                )
            ),
        )
        sr = SrConfig(
            url=_ask_or_cancel(
                questionary.text(
                    "Schema Registry URL",
                    default=defaults.get("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
                )
            ),
        )

    # Phase 5 — KMS-specific
    kms_params: dict[str, str | None] = {}
    for field in _KMS_FIELDS[kms]:
        default = defaults.get(field.env_var, "")
        prompt = (
            questionary.password(f"{field.label} — Enter to skip")
            if field.secret
            else questionary.text(field.label, default=default)
        )
        raw = _ask_or_cancel(prompt)
        if kms == "gcp" and field.config_key == "private_key":
            cleaned = sanitize_gcp_private_key(raw)
        else:
            cleaned = raw.strip()
        kms_params[field.config_key] = _optional(cleaned)

    # Phase 6 — output dir
    default_output = repo_root / "generated" / project_name
    output_str = _ask_or_cancel(
        questionary.path("Output directory", default=str(default_output), only_directories=True)
    )
    output_dir = Path(output_str).expanduser().resolve()

    if output_dir.exists() and any(output_dir.iterdir()):
        if not _ask_or_cancel(
            questionary.confirm(
                f"{output_dir} is not empty — overwrite files in it?",
                default=False,
            )
        ):
            raise WizardCancelled()

    # Build the config now so the summary can show derived names (topic, kek_name, …)
    config = GenerationConfig(
        project_name=project_name,
        description=description,
        language=language,
        target=target,
        kms=kms,
        kafka=kafka,
        schema_registry=sr,
        kms_params=kms_params,
    )

    # Phase 7 — summary + confirm
    table = Table(title="Generation summary", show_header=False)
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    table.add_row("Project", project_name)
    table.add_row("Language", language)
    table.add_row("Target", target)
    table.add_row("KMS", _KMS_LABELS[kms])
    table.add_row("Bootstrap", kafka.bootstrap_servers)
    table.add_row("Schema Registry", sr.url)
    table.add_row("Topic", config.topic)
    table.add_row("Consumer group", config.group_id)
    table.add_row("KEK name", config.kek_name)
    table.add_row("Output dir", str(output_dir))
    missing = [f.config_key for f in _KMS_FIELDS[kms] if kms_params[f.config_key] is None]
    if missing:
        table.add_row("[yellow]Skipped (will be <FILL_ME>)[/yellow]", ", ".join(missing))
    console.print(table)

    if not _ask_or_cancel(questionary.confirm("Generate?", default=True)):
        raise WizardCancelled()

    return config, output_dir
