"""Custom exception hierarchy for the candidate transformer pipeline.

Design principle: every exception is specific enough for callers to handle
individually, but inherits from a common base for blanket catching at the
CLI boundary. We never use bare `Exception`.
"""


class CandidateTransformerError(Exception):
    """Base exception for all candidate-transformer errors."""


# ---------------------------------------------------------------------------
# Source & file errors
# ---------------------------------------------------------------------------


class SourceDetectionError(CandidateTransformerError):
    """Raised when a file's source type cannot be determined."""


class FileReadError(CandidateTransformerError):
    """Raised when a file cannot be read (missing, permissions, corrupted)."""


# ---------------------------------------------------------------------------
# Parsing errors
# ---------------------------------------------------------------------------


class ParseError(CandidateTransformerError):
    """Raised when a source file cannot be parsed into raw candidate data."""


class MalformedCSVError(ParseError):
    """Raised when a CSV file has structural issues (missing headers, bad encoding)."""


class PDFExtractionError(ParseError):
    """Raised when PDF text extraction fails."""


# ---------------------------------------------------------------------------
# Normalization errors
# ---------------------------------------------------------------------------


class NormalizationError(CandidateTransformerError):
    """Raised when a field value cannot be normalized."""


class InvalidPhoneError(NormalizationError):
    """Raised when a phone number cannot be parsed or validated."""


class InvalidEmailError(NormalizationError):
    """Raised when an email address fails validation."""


class InvalidDateError(NormalizationError):
    """Raised when a date string cannot be parsed."""


# ---------------------------------------------------------------------------
# Merge errors
# ---------------------------------------------------------------------------


class MergeError(CandidateTransformerError):
    """Raised when candidate merging encounters an unrecoverable issue."""


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class ConfigurationError(CandidateTransformerError):
    """Raised when projection config is invalid."""


class ProjectionError(CandidateTransformerError):
    """Raised when a projection operation fails (bad path, type mismatch)."""


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class ValidationError(CandidateTransformerError):
    """Raised when final output fails schema validation."""
