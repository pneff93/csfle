"""Rich-rendered post-generation summary shown after `csfle-gen new` completes."""
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree

from csfle_gen.models import GenerationConfig
from csfle_gen.renderer import PLACEHOLDER

CONSOLE = Console()

LANG_STEPS: dict[str, dict[str, tuple[str, str] | str]] = {
    "java": {
        "setup": ("Build the project", "mvn clean compile"),
        "produce": 'mvn exec:java -Dexec.mainClass="com.example.app.BasicProducer"',
        "consume": 'mvn exec:java -Dexec.mainClass="com.example.app.BasicConsumer"',
    },
    "javascript": {
        "setup": ("Install dependencies", "npm install"),
        "produce": "npm run produce",
        "consume": "npm run consume",
    },
    "dotnet": {
        "setup": ("Build the projects", "dotnet build Producer\ndotnet build Consumer"),
        "produce": "dotnet run --project Producer",
        "consume": "dotnet run --project Consumer",
    },
    "go": {
        "setup": ("Download module dependencies", "go mod tidy"),
        "produce": "go run ./cmd/producer",
        "consume": "go run ./cmd/consumer",
    },
    "python": {
        "setup": ("Install dependencies", "pip install -r requirements.txt"),
        "produce": "python avro_producer.py",
        "consume": "python avro_consumer.py",
    },
}


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


def print_next_steps(
    config: GenerationConfig,
    output_dir: Path,
    written: list[Path],
    generator_dir: Path,
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
        CONSOLE.print(f"[yellow] ⚠️ Fill these placeholders in {output_dir}/.env before running:[/yellow]")
        for key in missing:
            CONSOLE.print(f"  • [bold]{key}[/bold]")

    cwd = Path.cwd()
    rel_to_cwd = output_dir.relative_to(cwd) if output_dir.is_relative_to(cwd) else output_dir

    lang = LANG_STEPS.get(config.language, LANG_STEPS["python"])
    setup_label, setup_cmd = lang["setup"]
    steps: list[tuple[str, str]] = [
        (setup_label, f"cd {rel_to_cwd}\n{setup_cmd}"),
    ]

    if config.target == "platform":
        compose_dir = generator_dir.relative_to(cwd) if generator_dir.is_relative_to(cwd) else generator_dir
        steps.append((
            "Start Confluent Platform (in another terminal or background)",
            f"(cd {compose_dir.as_posix()} && docker compose up -d)",
        ))

    steps.extend([
        ("Create the topic + register schema and encryption rule", "./bootstrap.sh"),
        ("Produce encrypted records", lang["produce"]),
        ("Consume + decrypt (in another terminal)", lang["consume"]),
    ])

    CONSOLE.print()
    CONSOLE.print("[bold]Next steps:[/bold]")
    for i, (label, cmd) in enumerate(steps, start=1):
        CONSOLE.print(f"\n  [bold cyan]{i}.[/bold cyan] {label}")
        CONSOLE.print(_bash(cmd))

    CONSOLE.print()
    CONSOLE.print(f"[dim]Full reference: {rel_to_cwd / 'README.md'}[/dim]")
