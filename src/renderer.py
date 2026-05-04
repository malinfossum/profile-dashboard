"""Markdown rendering. Each section is a pure function returning a string."""

from __future__ import annotations

from datetime import UTC, datetime

MARKER_START = "<!-- DASHBOARD:START -->"
MARKER_END = "<!-- DASHBOARD:END -->"

FEATURED_LIMIT = 5
EMPTY_FIELD = "—"


def _escape_cell(text: str | None) -> str:
    if not text:
        return EMPTY_FIELD
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("`", "\\`")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _format_date(iso_ts: str | None) -> str:
    if not iso_ts:
        return EMPTY_FIELD
    return iso_ts[:10]  # ISO 8601 → YYYY-MM-DD


def render_featured_table(featured: list[dict]) -> str:
    header = "| Project | About | Lang | Updated |\n|---|---|---|---|"
    if not featured:
        return f"{header}\n| _No featured repos yet_ | | | |"
    rows = []
    for repo in featured[:FEATURED_LIMIT]:
        name = _escape_cell(repo.get("name"))
        url = repo.get("html_url", "")
        about = _escape_cell(repo.get("description"))
        lang = _escape_cell(repo.get("language"))
        updated = _format_date(repo.get("pushed_at"))
        rows.append(f"| [{name}]({url}) | {about} | {lang} | {updated} |")
    return header + "\n" + "\n".join(rows)


def render_stats_line(repo_count: int, languages: list[str], generated_at: datetime) -> str:
    langs = ", ".join(languages) if languages else EMPTY_FIELD
    when = generated_at.strftime("%Y-%m-%d")
    return (
        f"**Stats:** {repo_count} public repos · Top languages: {langs} · Last updated {when} (UTC)"
    )


def compose(
    featured: list[dict],
    repo_count: int,
    languages: list[str],
    generated_at: datetime | None = None,
) -> str:
    """Build the full block (without markers) from prepared data."""
    when = generated_at or datetime.now(UTC)
    sections = [
        "### What I'm building",
        "",
        render_featured_table(featured),
        "",
        render_stats_line(repo_count, languages, when),
    ]
    return "\n".join(sections)


def wrap_with_markers(block: str) -> str:
    return f"{MARKER_START}\n{block}\n{MARKER_END}"
