"""Output truncation utilities for tool results."""

from __future__ import annotations

TRUNCATION_NOTICE = "\n... (output truncated)"


def truncate_text(text: str, max_bytes: int = 20000) -> tuple[str, bool]:
    """Truncate text to a maximum byte size.

    Args:
        text: The text to potentially truncate.
        max_bytes: Maximum number of bytes (default: 20000).

    Returns:
        Tuple of (truncated_text, was_truncated).
    """
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text, False

    # Truncate and decode safely
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + TRUNCATION_NOTICE, True
