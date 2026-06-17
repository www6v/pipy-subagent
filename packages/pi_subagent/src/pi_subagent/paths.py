"""Filesystem paths for piPy extension wiring."""

from __future__ import annotations

import os
from pathlib import Path


def default_extension_path() -> Path:
    """Default subagent_extension.py relative to this package repo layout."""
    return (
        Path(__file__).resolve().parents[4]
        / "extensions"
        / "subagent_extension.py"
    )


def resolve_extension_path() -> Path:
    """Resolve extension path from PIPY_SUBAGENT_EXTENSION or default."""
    explicit = os.environ.get("PIPY_SUBAGENT_EXTENSION")
    if explicit:
        return Path(explicit)
    return default_extension_path()
