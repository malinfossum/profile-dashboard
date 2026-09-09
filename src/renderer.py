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

# Star badge geometry. The badge is a miniature of the merged-PRs pill, so the
# two read as one family. SVG has no shrink-to-fit, so the width is measured
# from the label rather than set once.
STAR_CAPSULE_HEIGHT = 18
# HTML's legacy align="middle" centres an image on the text baseline - not on
# the optical centre of the text, the way CSS vertical-align: middle would. That
# left the capsule sitting 4px low. Transparent space below the capsule lifts it
# by half the padding, so 8px lands it dead on. Measured against GitHub's own
# rendered HTML, not estimated: see docs/design.md.
STAR_BADGE_PAD_BOTTOM = 8
STAR_BADGE_HEIGHT = STAR_CAPSULE_HEIGHT + STAR_BADGE_PAD_BOTTOM
# Open space instead of a separator glyph. Consecutive plain spaces collapse in
# HTML, so the air has to come from entities.
GAP = "&ensp;&nbsp;"
# Advance widths at font-size 11, measured from the rendered font rather than
# assumed - digits are not one width ("1" is 3.85, "0" is 6.04), and guessing a
# flat average left the wide labels visibly lopsided.
_GLYPH_ADVANCE = {
    "0": 6.042,
    "1": 3.846,
    "2": 5.081,
    "3": 5.344,
    "4": 5.865,
    "5": 5.403,
    "6": 6.069,
    "7": 5.199,
    "8": 6.053,
    "9": 6.032,
    ".": 2.771,
    "k": 5.371,
}
_FALLBACK_ADVANCE = 6.042

# Five-point star. cy is 9.477, not 9, because the ink has to be centred and a
# star's ink is not symmetric about its geometric centre - the single top point
# reaches further than the two bottom ones. Centring the geometry left the star
# sitting ~1px above the digits.
_STAR_PATH = (
    "M11.00 4.48 L12.29 7.70 L15.76 7.93 L13.09 10.16 L13.94 13.52 "
    "L11.00 11.68 L8.06 13.52 L8.91 10.16 L6.24 7.93 L9.71 7.70 Z"
)
_STAR_INK_RIGHT = 15.76
# Constant space between the star and the number, so every badge reads alike.
_STAR_TEXT_GAP = 5.0
_TEXT_X = _STAR_INK_RIGHT + _STAR_TEXT_GAP
# Matches the star's left inset (6.24), so the pair sits centred.
_PAD_RIGHT = 6.25
# Digit cap ascent is 7.0 at font-size 11, so this baseline puts the cap centre
# on y=9 - the capsule's centre line, and the star's ink centre.
_TEXT_BASELINE = 12.5


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


def star_asset_name(stars: int) -> str:
    """Filename for a star badge. Named by the label, so repos on the same
    count share one file and an unchanged count rewrites nothing."""
    return f"stars-{format_stars(stars)}.svg"


def star_badge_width(label: str) -> int:
    advance = sum(_GLYPH_ADVANCE.get(char, _FALLBACK_ADVANCE) for char in label)
    return round(_TEXT_X + advance + _PAD_RIGHT)


def _text_length(label: str) -> float:
    """Exact width the number is drawn at.

    The advance table is one font's metrics, but the badge renders in whatever
    font the reader has. Pinning textLength makes the geometry identical either
    way: the star-to-number gap and the right padding stay constant, and only
    sub-pixel glyph scaling absorbs the difference.
    """
    return round(star_badge_width(label) - _TEXT_X - _PAD_RIGHT, 2)


def render_star_badge_svg(stars: int) -> str:
    """A self-hosted star badge in the profile palette. No third-party service."""
    label = format_stars(stars)
    width = star_badge_width(label)
    noun = "star" if stars == 1 else "stars"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {STAR_BADGE_HEIGHT}"
     width="{width}" height="{STAR_BADGE_HEIGHT}" role="img" aria-label="{label} {noun}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{STAR_CAPSULE_HEIGHT - 1}" rx="8.5"
        fill="#14110d" stroke="#c9a96e" stroke-opacity="0.55" stroke-width="1"/>
  <path d="{_STAR_PATH}" fill="#c9a96e"/>
  <text x="{_TEXT_X:g}" y="{_TEXT_BASELINE:g}" textLength="{_text_length(label):g}"
        lengthAdjust="spacingAndGlyphs" fill="#f0ebe4"
        font-family="'Optima', 'Candara', 'Calibri', 'Segoe UI', system-ui, sans-serif"
        font-size="11">{label}</text>
</svg>
"""


def _star_badge_img(stars: int) -> str:
    """The badge as an inline <img>, or an empty string for an unstarred repo."""
    if stars < 1:
        return ""
    label = format_stars(stars)
    noun = "star" if stars == 1 else "stars"
    return (
        f'<img src="{ASSETS_PREFIX}/{star_asset_name(stars)}" '
        f'width="{star_badge_width(label)}" height="{STAR_BADGE_HEIGHT}" '
        f'align="middle" alt="{label} {noun}" />'
    )


def _project_line(repo: dict) -> str:
    name = escape(repo.get("name") or "")
    url = repo.get("html_url", "")
    stars = repo.get("stargazers_count") or 0
    badge = _star_badge_img(stars)
    star_part = f"{GAP}{badge}" if badge else ""
    about = escape(short_description(repo.get("description")))
    return f'<a href="{url}"><strong>{name}</strong></a>{star_part}{GAP}{about}'


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
    badge = _star_badge_img(stars)
    star_part = f"{GAP}{badge}" if badge else ""
    prs = sorted(repo["prs"], key=lambda p: p["number"])[:PRS_PER_REPO_LIMIT]
    links = " · ".join(f'<a href="{p["html_url"]}">#{p["number"]}</a>' for p in prs)
    return f'<a href="{repo["html_url"]}"><strong>{name}</strong></a>{star_part}{GAP}{links}'


def render_contrib_row(contrib_repos: list[dict], pr_count: int) -> str:
    chip, title, ethos = CONTRIB_GROUP
    noun = "pull request" if pr_count == 1 else "pull requests"
    pill = (
        f'<img src="{ASSETS_PREFIX}/oss-merged.svg" width="250" height="36" '
        f'alt="{pr_count} {noun} merged upstream" />'
    )
    # The <br/> paragraph gives the pill breathing room above the repo lines.
    lines = [pill, "<br/>"] + [_contrib_repo_line(r) for r in contrib_repos]
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
