"""Typer CLI interface for Multi-Source Candidate Data Transformer.

Provides user surface to run transformation pipeline with custom sources,
configs, and output destination.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from src.pipeline.pipeline import CandidateTransformerPipeline
from src.pipeline.validator import load_and_validate_config
from src.utils.exceptions import CandidateTransformerError
from src.utils.logging import configure_logging, get_logger

# Define typer app
app = typer.Typer(
    name="candidate-transformer",
    help="Multi-Source Candidate Data Transformer CLI.",
    add_completion=False,
)

logger = get_logger(__name__)


@app.command()
def transform(
    csv: Annotated[
        list[Path] | None,
        typer.Option(
            "--csv",
            help="Path to recruiter CSV export files. Can specify multiple times.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    resume: Annotated[
        list[Path] | None,
        typer.Option(
            "--resume",
            help="Path to candidate resume PDF files. Can specify multiple times.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    config_path: Annotated[
        Path,
        typer.Option(
            "--config",
            help="Path to the JSON output projection configuration file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = Path("config/default.json"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            help="Destination path to write the transformed candidate JSON profile(s).",
            file_okay=True,
            dir_okay=False,
            writable=True,
        ),
    ] = Path("output/result.json"),
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose/--no-verbose",
            "-v",
            help="Enable verbose output logging.",
        ),
    ] = False,
) -> None:
    """Ingest candidate data from CSV and PDF resume files, clean/merge, and output projected JSON."""
    # Configure logging level
    configure_logging(verbose=verbose)

    # Gather sources
    source_paths: list[Path] = []
    if csv:
        source_paths.extend(csv)
    if resume:
        source_paths.extend(resume)

    if not source_paths:
        typer.secho(
            "Error: No source files specified. Provide at least one --csv or --resume path.",
            fg=typer.colors.RED,
            bold=True,
            err=True,
        )
        raise typer.Exit(code=1)

    logger.info("Initializing pipeline with %d source files", len(source_paths))
    logger.debug("Source files: %s", [p.name for p in source_paths])

    try:
        # Load and validate configuration
        logger.info("Loading and validating configuration from %s", config_path)
        config = load_and_validate_config(config_path)

        # Run pipeline
        pipeline = CandidateTransformerPipeline()
        projected_profiles = pipeline.run(source_paths, config)

        # Write output to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(projected_profiles, f, indent=2, ensure_ascii=False)

        typer.secho(
            f"[OK] Pipeline run completed successfully. Written {len(projected_profiles)} profile(s) to {output_path}",
            fg=typer.colors.GREEN,
            bold=True,
        )

    except CandidateTransformerError as exc:
        typer.secho(
            f"Pipeline Error: {exc}",
            fg=typer.colors.RED,
            bold=True,
            err=True,
        )
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.secho(
            f"Unexpected system failure: {exc}",
            fg=typer.colors.RED,
            bold=True,
            err=True,
        )
        logger.error("CLI encounter unexpected exception", exc_info=True)
        raise typer.Exit(code=3) from exc


if __name__ == "__main__":
    app()
