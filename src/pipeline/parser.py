"""Base parser protocol and parser registry.

Defines the contract that every source parser must satisfy, and provides
a registry for dynamic parser lookup by source type.

Design decision: we use ``typing.Protocol`` rather than an ABC so that
parsers are structurally typed — any class with a matching ``parse``
method is a valid parser, no inheritance required. This makes it trivial
to add parsers in external packages without coupling to our class hierarchy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.models.candidate import ParsedCandidate
from src.utils.constants import SourceType
from src.utils.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class BaseParser(Protocol):
    """Protocol that all source parsers must satisfy.

    Each parser is responsible for:
    1. Reading a file of its designated type.
    2. Extracting raw candidate data into ``ParsedCandidate`` instances.
    3. Recording provenance for every extracted field.
    4. Handling malformed input gracefully (log + skip, never crash).
    """

    def parse(self, file_path: Path) -> list[ParsedCandidate]:
        """Parse a source file and return extracted candidate records.

        Args:
            file_path: Absolute or relative path to the source file.

        Returns:
            A list of ``ParsedCandidate`` instances. May be empty if the
            file contains no usable data. Each CSV row typically produces
            one entry; a PDF resume produces exactly one.

        Raises:
            FileReadError: If the file cannot be read.
            ParseError: If the file structure is fundamentally broken.
        """
        ...


class ParserRegistry:
    """Maps source types to parser instances.

    Usage::

        registry = ParserRegistry()
        registry.register(SourceType.CSV, CsvParser())
        registry.register(SourceType.PDF, PdfParser())

        parser = registry.get(SourceType.CSV)
        candidates = parser.parse(Path("data.csv"))

    Adding a new source type (e.g. DOCX, JSON) only requires:
    1. Implementing a class that satisfies ``BaseParser``.
    2. Calling ``registry.register(SourceType.NEW, MyParser())``.
    """

    def __init__(self) -> None:
        self._parsers: dict[SourceType, BaseParser] = {}

    def register(self, source_type: SourceType, parser: BaseParser) -> None:
        """Register a parser for a source type.

        Args:
            source_type: The source type this parser handles.
            parser: A parser instance satisfying the ``BaseParser`` protocol.

        Raises:
            TypeError: If ``parser`` does not satisfy ``BaseParser``.
        """
        if not isinstance(parser, BaseParser):
            raise TypeError(f"Parser {type(parser).__name__} does not satisfy BaseParser protocol")
        logger.debug("Registered parser %s for source type %s", type(parser).__name__, source_type)
        self._parsers[source_type] = parser

    def get(self, source_type: SourceType) -> BaseParser:
        """Look up the parser for a source type.

        Args:
            source_type: The source type to look up.

        Returns:
            The registered parser instance.

        Raises:
            KeyError: If no parser is registered for this source type.
        """
        if source_type not in self._parsers:
            raise KeyError(
                f"No parser registered for source type '{source_type}'. "
                f"Registered types: {list(self._parsers.keys())}"
            )
        return self._parsers[source_type]

    @property
    def supported_types(self) -> list[SourceType]:
        """Return list of source types with registered parsers."""
        return list(self._parsers.keys())
