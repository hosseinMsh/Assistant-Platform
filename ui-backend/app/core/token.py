"""Token normalization utilities."""
from __future__ import annotations


def normalize_token(raw: str) -> str:
    """Strip whitespace and 'Bearer ' prefix (case-insensitive).

    Accepts: "eyJ...", "Bearer eyJ...", "BEARER eyJ...", "  Bearer  eyJ...  "
    Returns the raw token string.
    Raises ValueError if the result is empty.
    """
    token = raw.strip()
    if token.lower().startswith("bearer"):
        # Remove "bearer" and any following whitespace
        token = token[6:].strip()
    if not token:
        raise ValueError("Access token must not be empty")
    return token
