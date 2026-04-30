"""Rich-rendered post-generation summary shown after `csfle-gen new` completes."""
import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree

from csfle_gen.models import GenerationConfig
from csfle_gen.renderer import PLACEHOLDER

CONSOLE = Console()

# projects/<project>/locations/<location>/keyRings/<ring>/cryptoKeys/<key>
_GCP_KEY_RE = re.compile(
    r"^projects/(?P<project>[^/]+)/locations/(?P<location>[^/]+)"
    r"/keyRings/(?P<keyring>[^/]+)/cryptoKeys/(?P<key>[^/]+)$"
)


def _file_tree(output_dir: Path, written: list[Path]) -> Tree:
    tree = Tree(f"[bold]{output_dir.name}/[/bold]")
    rels = sorted({p.relative_to(output_dir) for p in written})
    root = Path(".")
    nodes: dict[Path, Tree] = {root: tree}

    def _node_for(directory: Path) -> Tree:
        if directory in nodes:
            return nodes[directory]
        parent = _node_for(directory.parent if directory.parent != directory else root)
        nodes[directory] = parent.add(f"[cyan]{directory.name}/[/cyan]")
        return nodes[directory]

    for rel in rels:
        parent_dir = rel.parent if str(rel.parent) != "." else root
        _node_for(parent_dir).add(rel.name)
    return tree


def _scan_missing_secrets(env_path: Path) -> list[str]:
    if not env_path.is_file():
        return []
    missing: list[str] = []
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if value.strip() == PLACEHOLDER:
            missing.append(key.strip())
    return missing


def _bash(text: str) -> Syntax:
    return Syntax(text, "bash", background_color="default", padding=(0, 1))


def _gcp_iam_hint(config: GenerationConfig) -> str | None:
    """Return a faint reminder of the gcloud IAM binding required for the SA to use the KEK.

    Pre-fills the gcloud command from the values the user provided in the wizard,
    leaving `<placeholders>` for anything missing (skipped private-key fields, etc.).
    Returns None for non-GCP configs so the caller can `if hint: print(hint)`.
    """
    if config.kms != "gcp":
        return None

    parts = {"project": "<project>", "location": "<location>", "keyring": "<keyring>", "key": "<key>"}
    kms_key_id = config.kms_params.get("kms_key_id") or ""
    match = _GCP_KEY_RE.match(kms_key_id)
    if match:
        parts.update(match.groupdict())

    sa_email = config.kms_params.get("client_email") or "<service-account-email>"

    cmd = (
        f"gcloud kms keys add-iam-policy-binding {parts['key']} \\\n"
        f"  --keyring={parts['keyring']} \\\n"
        f"  --location={parts['location']} \\\n"
        f"  --project={parts['project']} \\\n"
        f'  --member="serviceAccount:{sa_email}" \\\n'
        f'  --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"'
    )
    indented = "\n".join(f"     {line}" for line in cmd.splitlines())
    return (
        "[dim]💡 The service account in `.env` needs permission to use the KEK. "
        "If it doesn't already, grant it:\n\n"
        f"{indented}\n[/dim]"
    )


def print_next_steps(
    config: GenerationConfig,
    output_dir: Path,
    written: list[Path],
    repo_root: Path,
) -> None:
    CONSOLE.print()
    CONSOLE.print(
        Panel(
            _file_tree(output_dir, written),
            title=f"[green]✓[/green] Generated {len(written)} files",
            border_style="green",
        )
    )

    missing = _scan_missing_secrets(output_dir / ".env")
    if missing:
        CONSOLE.print()
        CONSOLE.print("[yellow]⚠ Fill these placeholders in `.env` before running:[/yellow]")
        for key in missing:
            CONSOLE.print(f"  • [bold]{key}[/bold]")

    rel_to_repo = output_dir.relative_to(repo_root) if output_dir.is_relative_to(repo_root) else output_dir

    if config.language == "java":
        steps: list[tuple[str, str]] = [
            ("Build the project", f"cd {rel_to_repo}\nmvn clean compile"),
        ]
    elif config.language == "javascript":
        steps = [
            ("Install dependencies", f"cd {rel_to_repo}\nnpm install"),
        ]
    else:
        steps = [
            ("Install dependencies", f"cd {rel_to_repo}\npip install -r requirements.txt"),
        ]

    if config.target == "platform":
        platform_dir = (repo_root / "confluent_platform").relative_to(repo_root)
        steps.append((
            "Start Confluent Platform (in another terminal or background)",
            f"(cd {platform_dir.as_posix()} && docker compose up -d)",
        ))

    if config.language == "java":
        steps.extend([
            ("Create the topic + register schema and encryption rule", "./bootstrap.sh"),
            ("Produce encrypted records", 'mvn exec:java -Dexec.mainClass="com.example.app.BasicProducer"'),
            ("Consume + decrypt (in another terminal)", 'mvn exec:java -Dexec.mainClass="com.example.app.BasicConsumer"'),
        ])
    elif config.language == "javascript":
        steps.extend([
            ("Create the topic + register schema and encryption rule", "./bootstrap.sh"),
            ("Produce encrypted records", "npm run produce"),
            ("Consume + decrypt (in another terminal)", "npm run consume"),
        ])
    else:
        steps.extend([
            ("Create the topic + register schema and encryption rule", "./bootstrap.sh"),
            ("Produce encrypted records", "python avro_producer.py"),
            ("Consume + decrypt (in another terminal)", "python avro_consumer.py"),
        ])

    CONSOLE.print()
    CONSOLE.print("[bold]Next steps:[/bold]")
    for i, (label, cmd) in enumerate(steps, start=1):
        CONSOLE.print(f"\n  [bold cyan]{i}.[/bold cyan] {label}")
        CONSOLE.print(_bash(cmd))

    gcp_hint = _gcp_iam_hint(config)
    if gcp_hint:
        CONSOLE.print()
        CONSOLE.print(gcp_hint)

    CONSOLE.print()
    CONSOLE.print(f"[dim]Full reference: {rel_to_repo / 'README.md'}[/dim]")
