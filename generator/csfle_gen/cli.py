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

GENERATOR_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = GENERATOR_DIR / ".env"


@app.callback()
def _root() -> None:
    pass


@app.command()
def new() -> None:
    """Generate a new CSFLE client project interactively."""
    console = Console()

    try:
        config, output_dir = run_wizard(ENV_PATH)
    except WizardCancelled:
        console.print("[yellow]Cancelled 🛑[/yellow]")
        raise typer.Exit(1)

    written = render(config, output_dir)
    print_next_steps(config, output_dir, written, GENERATOR_DIR)
