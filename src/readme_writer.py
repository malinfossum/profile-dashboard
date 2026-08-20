"""Marker-based README replacement. Idempotent — only writes when content changes."""

from __future__ import annotations

from pathlib import Path

from src.renderer import MARKER_END, MARKER_START


class MarkersMissingError(Exception):
    """Raised when the target README does not contain both markers."""


def _replace_between_markers(content: str, new_block: str) -> str:
    start = content.find(MARKER_START)
    end = content.find(MARKER_END)
    if start == -1 or end == -1 or end < start:
        raise MarkersMissingError(
            f"Target README must contain both '{MARKER_START}' and '{MARKER_END}'. "
            "Add them once where you want the dashboard to appear."
        )
    end_inclusive = end + len(MARKER_END)
    return content[:start] + new_block + content[end_inclusive:]


def write_block(readme_path: Path, full_block_with_markers: str, dry_run: bool = False) -> bool:
    """Replace the dashboard block in the README. Returns True if the file changed."""
    content = readme_path.read_text(encoding="utf-8")
    new_content = _replace_between_markers(content, full_block_with_markers)
    if new_content == content:
        return False
    if not dry_run:
        readme_path.write_text(new_content, encoding="utf-8")
    return True


def write_text_file(path: Path, content: str, dry_run: bool = False) -> bool:
    """Write a text file only when the content differs. Returns True if changed."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    if not dry_run:
        path.write_text(content, encoding="utf-8", newline="\n")
    return True
