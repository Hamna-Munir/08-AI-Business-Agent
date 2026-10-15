"""
file_tools.py
Day 54: lets the agent read business files (notes, docs) for extra context —
restricted to a fixed allow-list of project directories so it can never be
pointed at an arbitrary path on the machine.
"""

from pathlib import Path
from typing import List

from . import config


class FileAccessError(Exception):
    pass


def _resolve_and_check(relative_path: str) -> Path:
    candidate = (config.ROOT_DIR / relative_path).resolve()
    allowed = [d.resolve() for d in config.FILE_TOOL_ALLOWED_DIRS]
    if not any(str(candidate).startswith(str(d)) for d in allowed):
        raise FileAccessError(
            f"'{relative_path}' is outside the allowed directories "
            f"({[str(d.name) for d in allowed]})."
        )
    if not candidate.exists():
        raise FileAccessError(f"'{relative_path}' does not exist.")
    return candidate


def list_business_files() -> List[str]:
    """Lists readable files across the allowed directories (data/, docs/, notes/)."""
    results = []
    for directory in config.FILE_TOOL_ALLOWED_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*")):
            if path.is_file():
                results.append(str(path.relative_to(config.ROOT_DIR)))
    return results


def read_business_file(relative_path: str, max_chars: int = 4000) -> str:
    """Reads a text file from data/, docs/, or notes/ only. CSVs are returned
    as raw text (the agent should prefer business_tools for querying data —
    this is for narrative files like docs/week-08-summary.md)."""
    path = _resolve_and_check(relative_path)
    try:
        text = path.read_text(errors="replace")
    except UnicodeDecodeError as e:
        raise FileAccessError(f"'{relative_path}' is not a readable text file.") from e
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... [truncated at {max_chars} chars]"
    return text
