from pathlib import Path

import typer
from rich.console import Console

from csfle_gen.instructions import print_next_steps
from csfle_gen.renderer import render
from csfle_gen.wizard import WizardCancelled, run_wizard

app = typer.Typer(
    name="csfle-gen",
    help="Interactive generator for CSFLE client projects.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _root() -> None:
    pass


def _find_repo_root(start: Path) -> Path:
    """Walk up from `start` until we find a dir with both confluent_platform/ and confluent_cloud/.

    These two siblings uniquely identify this repo. Falls back to `start` if not found
    (the generator can still run; discovery just won't find anything).
    """
    for candidate in [start, *start.parents]:
        if (candidate / "confluent_platform").is_dir() and (candidate / "confluent_cloud").is_dir():
            return candidate
    return start


@app.command()
def new() -> None:
    """Generate a new CSFLE client project interactively."""
    console = Console()
    repo_root = _find_repo_root(Path.cwd().resolve())

    try:
        config, output_dir = run_wizard(repo_root)
    except WizardCancelled:
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(1)

    written = render(config, output_dir)
    print_next_steps(config, output_dir, written, repo_root)
