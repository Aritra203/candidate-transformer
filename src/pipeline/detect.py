"""Source detection stage.

Classifies input files by file extension and maps them to standard SourceType enums.
Handles unknown file formats gracefully by raising SourceDetectionError.
"""

from __future__ import annotations

from pathlib import Path

from src.utils.constants import EXTENSION_TO_SOURCE, SourceType
from src.utils.exceptions import SourceDetectionError
from src.utils.logging import get_logger

logger = get_logger(__name__)


def detect_source_type(file_path: Path) -> SourceType:
    """Classifies the file's source type based on extension.

    Args:
        file_path: Path to the input candidate file.

    Returns:
        The detected SourceType.

    Raises:
        SourceDetectionError: If extension is not supported or missing.
    """
    ext = file_path.suffix.lower()
    if ext not in EXTENSION_TO_SOURCE:
        raise SourceDetectionError(
            f"Unsupported file extension '{ext}' for file '{file_path.name}'. "
            f"Supported extensions: {list(EXTENSION_TO_SOURCE.keys())}"
        )
    source_type = EXTENSION_TO_SOURCE[ext]
    logger.debug("Detected source type %s for file %s", source_type, file_path.name)
    return source_type
