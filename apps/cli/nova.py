from __future__ import annotations
import typer

app = typer.Typer(help="Nova CI-Rescue CLI (scaffold)")

@app.callback()
def main() -> None:
    """Nova CI-Rescue command-line interface.

    Commands will be added as implementation progresses.
    """
    pass

if __name__ == "__main__":
    app()
