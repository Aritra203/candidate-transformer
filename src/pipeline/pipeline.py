"""Pipeline orchestrator for Multi-Source Candidate Data Transformer.

Covers:
Input Files -> Detect -> Parse -> Normalize -> Merge -> Confidence -> Project -> Validate -> JSON
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.models.candidate import ParsedCandidate
from src.models.config import ProjectionConfig
from src.parsers.csv_parser import CsvParser
from src.parsers.pdf_parser import PdfParser
from src.pipeline.confidence import compute_confidence
from src.pipeline.detect import detect_source_type
from src.pipeline.merger import merge_candidates
from src.pipeline.normalizer import normalize_candidate
from src.pipeline.parser import ParserRegistry
from src.pipeline.projection import project
from src.pipeline.validator import validate_output
from src.utils.constants import SourceType
from src.utils.exceptions import CandidateTransformerError, FileReadError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CandidateTransformerPipeline:
    """Orchestrator class for running the full candidate data transformation pipeline."""

    def __init__(self) -> None:
        # Initialize registry and register standard parsers
        self.registry = ParserRegistry()
        self.registry.register(SourceType.CSV, CsvParser())
        self.registry.register(SourceType.PDF, PdfParser())

    def run(
        self,
        source_paths: list[Path],
        config: ProjectionConfig,
    ) -> list[dict[str, Any]]:
        """Executes the pipeline on a list of input files using a projection configuration.

        Args:
            source_paths: List of input file paths.
            config: Validated runtime projection configuration.

        Returns:
            A list of projected JSON-compatible dictionaries (one per unique candidate).
        """
        parsed_candidates: list[ParsedCandidate] = []

        # Step 1: Detect & Parse & Extract & Normalize per file
        for path in source_paths:
            if not path.exists():
                logger.error("Input file not found: %s", path)
                raise FileReadError(f"Input file not found: {path}")

            try:
                source_type = detect_source_type(path)
                parser = self.registry.get(source_type)
                logger.info("Parsing file %s with %s", path.name, type(parser).__name__)
                extracted = parser.parse(path)

                for candidate in extracted:
                    # Normalize in-place immediately after parsing
                    normalized = normalize_candidate(candidate)
                    parsed_candidates.append(normalized)

            except CandidateTransformerError as exc:
                logger.warning("Pipeline skipping file %s due to error: %s", path.name, exc)
                # We continue processing other files rather than failing the whole run
                continue
            except Exception as exc:
                logger.error(
                    "Unexpected failure parsing file %s: %s", path.name, exc, exc_info=True
                )
                continue

        if not parsed_candidates:
            logger.warning("No candidate records were successfully parsed from any sources.")
            return []

        # Step 2: Merge Engine (Deduplicate & Resolve Conflicts)
        logger.info("Merging %d parsed candidates...", len(parsed_candidates))
        merged_profiles = merge_candidates(parsed_candidates)

        # Step 3: Confidence & Projection & Validation
        projected_outputs: list[dict[str, Any]] = []
        for profile in merged_profiles:
            # Score overall confidence
            profile_with_confidence = compute_confidence(profile)

            # Project output
            logger.info(
                "Projecting profile candidate_id=%s...", profile_with_confidence.candidate_id[:12]
            )
            projected = project(profile_with_confidence, config)

            # Validate projected output schema
            validate_output(projected, config)
            projected_outputs.append(projected)

        return projected_outputs
