"""HTML/markdown rendering. Each section is a pure function returning a string."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape

MARKER_START = "<!-- DASHBOARD:START -->"
MARKER_END = "<!-- DASHBOARD:END -->"

# Presentation for the purpose groups. Keys are what --group uses on the CLI;
# row order in the table follows the order the CLI args are given in.
GROUPS = {
    "focus": ("chip-gold", "For focus", "Calm tools, built for brains like mine."),
    "wellbeing": ("chip-terracotta", "For wellbeing", "Making life a little easier."),
    "momentum": ("chip-teal", "For momentum", "Keeping the work visible and moving."),
}
CONTRIB_GROUP = ("chip-purple", "For everyone", "Open source: showing up for the tools we share.")

ASSETS_PREFIX = "assets"
PRS_PER_REPO_LIMIT = 4


def short_description(text: str | None) -> str:
    """First sentence of a repo description, first letter lowercased.

    The lowercase step is skipped when the second character is also uppercase,
    so acronym openers like "ADHD-friendly" keep their casing.
    """
    if not text:
        return ""
    text = text.strip()
    first = text.split(". ")[0].rstrip(".") + "."
    if len(first) >= 2 and first[0].isupper() and not first[1].isupper():
        first = first[0].lower() + first[1:]
    return first


def format_stars(count: int) -> str:
    if count < 1000:
        return str(count)
    value = f"{count / 1000:.1f}".removesuffix(".0")
    return f"{value}k"


def _chip_img(chip: str) -> str:
    return f'<img src="{ASSETS_PREFIX}/{chip}.svg" width="14" height="14" alt="" />'


def _dot_img() -> str:
    return f'<img src="{ASSETS_PREFIX}/dot-gold.svg" width="10" height="10" alt="·" />'


def _project_line(repo: dict) -> str:
    name = escape(repo.get("name") or "")
    url = repo.get("html_url", "")
    stars = repo.get("stargazers_count") or 0
    star_part = f" ★ {stars}" if stars > 0 else ""
    about = escape(short_description(repo.get("description")))
    return f'<a href="{url}"><strong>{name}</strong></a>{star_part}: {about}'


def _group_cell(chip: str, title: str, ethos: str) -> str:
    return (
        f'<td valign="middle" width="30%">\n\n'
        f"{_chip_img(chip)} <strong>{title}</strong>\n\n"
        f"<em>{ethos}</em>\n\n"
        f"</td>"
    )


def _projects_cell(lines: list[str]) -> str:
    body = "\n\n".join(lines)
    return f'<td valign="top" width="70%">\n\n{body}\n\n</td>'


def render_group_row(key: str, repos: list[dict]) -> str:
    chip, title, ethos = GROUPS[key]
    lines = [_project_line(r) for r in repos]
    return f"<tr>\n{_group_cell(chip, title, ethos)}\n{_projects_cell(lines)}\n</tr>"


def _contrib_repo_line(repo: dict) -> str:
    name = escape(repo["full_name"])
    stars = repo.get("stargazers_count") or 0
    star_part = f" ★ {format_stars(stars)}" if stars > 0 else ""
    prs = sorted(repo["prs"], key=lambda p: p["number"])[:PRS_PER_REPO_LIMIT]
    links = " · ".join(f'<a href="{p["html_url"]}">#{p["number"]}</a>' for p in prs)
    return f'<a href="{repo["html_url"]}"><strong>{name}</strong></a>{star_part}: {links}'


def render_contrib_row(contrib_repos: list[dict], pr_count: int) -> str:
    chip, title, ethos = CONTRIB_GROUP
    noun = "pull request" if pr_count == 1 else "pull requests"
    pill = (
        f'<img src="{ASSETS_PREFIX}/oss-merged.svg" width="250" height="36" '
        f'alt="{pr_count} {noun} merged upstream" />'
    )
    lines = [pill] + [_contrib_repo_line(r) for r in contrib_repos]
    return f"<tr>\n{_group_cell(chip, title, ethos)}\n{_projects_cell(lines)}\n</tr>"


def render_stats_line(repo_count: int, languages: list[str], generated_at: datetime) -> str:
    lang_pills = " ".join(f"<code>{escape(lang)}</code>" for lang in languages)
    when = generated_at.strftime("%Y-%m-%d")
    return (
        f'<p align="center"><code>{repo_count} original projects</code> {_dot_img()} '
        f"{lang_pills} {_dot_img()} <code>updated {when}</code></p>"
    )


def render_oss_pill_svg(pr_count: int) -> str:
    """The self-hosted merged-PRs pill, regenerated so the count stays current."""
    noun = "pull request" if pr_count == 1 else "pull requests"
    label = f"{pr_count} PRs MERGED UPSTREAM" if pr_count != 1 else "1 PR MERGED UPSTREAM"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 36" width="250" height="36"
     role="img" aria-label="{pr_count} {noun} merged upstream">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="90%">
      <stop offset="0%" stop-color="#14110d"/>
      <stop offset="100%" stop-color="#0a0908"/>
    </radialGradient>
  </defs>
  <rect x="0.5" y="0.5" width="249" height="35" rx="17.5" fill="url(#bg)"
        stroke="#c9a96e" stroke-opacity="0.55" stroke-width="1"/>
  <path d="M30 13 L35 18 L30 23 L25 18 Z" fill="#c9a96e"/>
  <text x="140" y="22.5" text-anchor="middle" fill="#f0ebe4"
        font-family="'Optima', 'Candara', 'Calibri', 'Segoe UI', system-ui, sans-serif"
        font-size="13" letter-spacing="2">{label}</text>
</svg>
'''


def compose(
    grouped: list[tuple[str, list[dict]]],
    contrib_repos: list[dict],
    pr_count: int,
    repo_count: int,
    languages: list[str],
    generated_at: datetime | None = None,
) -> str:
    """Build the full block (without markers) from prepared data.

    The block contains data only — no section heading. The target README owns
    its own structure and decides what heading (if any) sits above the markers.
    """
    when = generated_at or datetime.now(UTC)
    rows = [render_group_row(key, repos) for key, repos in grouped]
    if contrib_repos:
        rows.append(render_contrib_row(contrib_repos, pr_count))
    table = '<table align="center">\n' + "\n".join(rows) + "\n</table>"
    return f"{table}\n\n{render_stats_line(repo_count, languages, when)}"


def wrap_with_markers(block: str) -> str:
    return f"{MARKER_START}\n{block}\n{MARKER_END}"
