import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, nodes

from csfle_gen.models import GenerationConfig

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Per-language macro contracts.  Each language template tree composes templates
# differently, so the required slot names diverge: Python wants `pip_deps`, Java
# wants `dependencies`, etc.
LANGUAGE_MACRO_CONTRACT: dict[str, dict[str, frozenset[str]]] = {
    "python": {
        "kms": frozenset(
            {
                "imports",
                "register",
                "setup_credentials",
                "executor_params",
                "env_vars",
                "pip_deps",
                "readme_section",
                "kms_type",
            }
        ),
        "target": frozenset(
            {
                "kafka_config",
                "sr_config",
                "env_vars",
                "readme_section",
            }
        ),
    },
    "java": {
        "kms": frozenset(
            {
                "dependencies",
                "executor_params",
                "config_methods",
                "validate_calls",
                "env_vars",
                "kms_type",
                "readme_section",
            }
        ),
        "target": frozenset(
            {
                "kafka_security",
                "sr_security",
                "config_methods",
                "validate_calls",
                "env_vars",
                "readme_section",
            }
        ),
    },
    "javascript": {
        "kms": frozenset(
            {
                "driver_class",
                "rule_config",
                "config_validate_keys",
                "env_vars",
                "kms_type",
                "readme_section",
            }
        ),
        "target": frozenset(
            {
                "kafka_options",
                "sr_options",
                "config_validate_keys",
                "env_vars",
                "readme_section",
            }
        ),
    },
    "dotnet": {
        "kms": frozenset(
            {
                "driver_using",
                "driver_class",
                "package_reference",
                "rule_config_method",
                "rule_config_method_call",
                "config_validate_keys",
                "env_vars",
                "kms_type",
                "readme_section",
            }
        ),
        "target": frozenset(
            {
                "producer_config_extras",
                "sr_config_extras",
                "config_validate_keys",
                "env_vars",
                "readme_section",
            }
        ),
    },
    "go": {
        "kms": frozenset(
            {
                "driver_import",
                "driver_register",
                "rule_config_func",
                "rule_config_func_call",
                "config_validate_keys",
                "env_vars",
                "kms_type",
                "readme_section",
            }
        ),
        "target": frozenset(
            {
                "kafka_extras",
                "sr_extras",
                "config_validate_keys",
                "env_vars",
                "readme_section",
            }
        ),
    },
}

PLACEHOLDER = "<FILL_ME>"

KMS_LABELS = {
    "aws": "AWS KMS",
    "azure": "Azure Key Vault",
    "gcp": "Google Cloud KMS",
    "hashicorp": "HashiCorp Vault",
}

KMS_ENV_PREFIXES = {
    "aws": "AWS",
    "azure": "AZURE",
    "gcp": "GCP",
    "hashicorp": "HCVAULT",
}

TARGET_LABELS = {
    "cloud": "Confluent Cloud",
    "platform": "Confluent Platform",
}


class MacroContractError(Exception):
    pass


def _tab_indent_filter(text: str, count: int = 1) -> str:
    """Indent every line *except the first* by `count` tab characters.

    Mirrors Jinja2's built-in `| indent(n)` (which uses spaces) but with tabs,
    so it can be used inside Go templates where tabs are the idiomatic indent.
    """
    lines = text.splitlines()
    if not lines:
        return text
    pad = "\t" * count
    head, *tail = lines
    rendered = "\n".join([head] + [(pad + line if line else line) for line in tail])
    if text.endswith("\n"):
        rendered += "\n"
    return rendered


def _env_keys_filter(text: str) -> str:
    """Convert a KEY=VALUE block into `_get_env('KEY')` lines, preserving order.

    Strips comments and blank lines. Used by config.py.j2 to derive validate_config()
    from the same env_vars() macro that populates .env.example.
    """
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        out.append(f"_get_env('{key}')")
    return "\n".join(out)


def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["env_keys"] = _env_keys_filter
    env.filters["tab_indent"] = _tab_indent_filter
    return env


def _macros_in(env: Environment, source: str) -> set[str]:
    ast = env.parse(source)
    return {n.name for n in ast.find_all(nodes.Macro)}


def _validate_macros(env: Environment, language: str) -> None:
    partials_dir = TEMPLATES_DIR / language / "partials"
    if not partials_dir.is_dir():
        return
    contract = LANGUAGE_MACRO_CONTRACT.get(language, {})
    for partial in sorted(partials_dir.glob("*.j2")):
        prefix = partial.stem.split("_", 1)[0]
        required = contract.get(prefix)
        if required is None:
            continue
        defined = _macros_in(env, partial.read_text())
        missing = required - defined
        if missing:
            raise MacroContractError(
                f"{partial.stem} is missing required macros: {sorted(missing)}"
            )


def _placeholder_config(config: GenerationConfig) -> GenerationConfig:
    """Return a copy of config with all secret-bearing fields replaced by placeholders.

    Used to render `.env.example` (snapshot-stable, no real values).
    """
    data = config.model_dump()
    data["kafka"]["sasl_username"] = PLACEHOLDER if config.kafka.sasl_username is not None else None
    data["kafka"]["sasl_password"] = PLACEHOLDER if config.kafka.sasl_password is not None else None
    data["schema_registry"]["basic_auth_user_info"] = (
        PLACEHOLDER if config.schema_registry.basic_auth_user_info is not None else None
    )
    data["kms_params"] = {k: PLACEHOLDER for k in config.kms_params}
    return GenerationConfig(**data)


def _context(config: GenerationConfig) -> dict:
    return {
        "config": config,
        "language": config.language,
        "kms": config.kms,
        "target": config.target,
        "kms_label": KMS_LABELS[config.kms],
        "kms_env_prefix": KMS_ENV_PREFIXES[config.kms],
        "target_label": TARGET_LABELS[config.target],
        **config.model_dump(),
    }


def _emit_tree(
    src_root: Path,
    output_dir: Path,
    env: Environment,
    config: GenerationConfig,
    written: list[Path],
    seen_rels: set[Path],
) -> None:
    """Walk one source tree and emit each file into output_dir.

    `.j2` files are rendered (with `.env.example.j2` also emitting `.env` in the
    same pass); other files are copied verbatim. Tracks `seen_rels` to enforce
    that no two source trees ever produce the same output path.
    """
    if not src_root.is_dir():
        return
    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root)
        dst = output_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.name == ".env.example.j2":
            template_name = str(src.relative_to(TEMPLATES_DIR))
            template = env.get_template(template_name)

            for out_rel, ctx in (
                (rel.with_suffix(""), _context(_placeholder_config(config))),
                (Path(".env"), _context(config)),
            ):
                if out_rel in seen_rels:
                    raise RuntimeError(f"Duplicate output path from template trees: {out_rel}")
                seen_rels.add(out_rel)
                (output_dir / out_rel).write_text(template.render(ctx))
                written.append(output_dir / out_rel)
        elif src.suffix == ".j2":
            template_name = str(src.relative_to(TEMPLATES_DIR))
            template = env.get_template(template_name)
            out_rel = rel.with_suffix("")
            if out_rel in seen_rels:
                raise RuntimeError(f"Duplicate output path from template trees: {out_rel}")
            seen_rels.add(out_rel)
            out_path = output_dir / out_rel
            out_path.write_text(template.render(_context(config)))
            if out_path.suffix == ".sh":
                out_path.chmod(0o755)
            written.append(out_path)
        else:
            if rel in seen_rels:
                raise RuntimeError(f"Duplicate output path from template trees: {rel}")
            seen_rels.add(rel)
            shutil.copy2(src, dst)
            written.append(dst)


def render(config: GenerationConfig, output_dir: Path) -> list[Path]:
    language = config.language
    env = _build_env()
    _validate_macros(env, language)

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    seen_rels: set[Path] = set()

    # Language-specific tree first, then the common tree shared across all languages.
    _emit_tree(TEMPLATES_DIR / language / "shared", output_dir, env, config, written, seen_rels)
    _emit_tree(TEMPLATES_DIR / "_common", output_dir, env, config, written, seen_rels)

    return written
