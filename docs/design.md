# Design — profile-dashboard

The "why" behind the structure, captured for future maintenance.

## Goal

Render a curated dashboard inside `malinfossum/malinfossum/README.md`, refreshed daily, without manual edits.

## Architecture

Five focused modules. Each has one job, and the network and filesystem are isolated to single files so the rest is pure and testable.

```
github_client  ──fetch──▶  stats  ──aggregate──▶  renderer  ──compose──▶  readme_writer
   (network)                (pure)                 (pure)                   (filesystem)
```

`main.py` orchestrates the pipeline top-down. Nothing else calls between modules.

| Module | Pure? | Touches |
|---|---|---|
| `github_client.py` | No | Network |
| `stats.py` | Yes | — |
| `renderer.py` | Yes | — |
| `readme_writer.py` | No | Filesystem |
| `main.py` | No | Env, args |

This mirrors MVC: client + stats are the model, renderer is the view, main is the controller.

## Discipline that keeps this maintainable

- **Renderers never call the API.** If a section needs new data, add an aggregator first.
- **Stats never format strings.** All Markdown output lives in `renderer.py`.
- **`readme_writer` doesn't know what the block contains.** It only handles markers.

These three rules are why adding a new section (e.g., a commit-history sparkline) doesn't touch existing code: new fetcher → new aggregator → new render function → wire it into `main.py`. Existing modules stay closed.

## Idempotence

The script computes the full block in memory, then asks the writer to replace between markers. If the new content is byte-identical to the old, nothing is written and the workflow doesn't commit. This is why the dashboard uses absolute UTC dates instead of relative ones — relative dates would force a daily commit even when nothing changed.

## Security posture

- A **fine-grained PAT** scoped to a single repo with a single permission. Stored as `PROFILE_README_TOKEN`. 90-day expiration enforces rotation.
- Workflow `permissions:` defaults to read-only; the cross-repo write uses the PAT, not `GITHUB_TOKEN`.
- `concurrency:` prevents cron + manual overlap.
- Auto-commits use the GitHub Actions bot identity, never a personal email.
- `[skip ci]` in commit messages prevents future workflow loops.
- Renderer escapes Markdown special characters in any field sourced from the API.
- No token, headers, or full API responses are ever logged.

## Action version pinning

Workflows use floating major tags (`actions/checkout@v6`) and rely on **Dependabot** for the `github-actions` ecosystem to propose updates as PRs. This is simpler to maintain than hard-pinned SHAs and keeps the project current. If a stricter posture is wanted later, replace tags with full commit SHAs and let Dependabot manage them — same workflow, same Dependabot config.

## Generated images

The profile README pulls in **no third-party services** — no shields.io, no stats widgets. Every
badge is an SVG this tool generates and commits into the profile repo, so the page makes no
external request and cannot break when someone else's service does.

That costs a little machinery: the merged-PRs pill (`--pill-path`) and the star badges
(`--assets-dir`). Star badges are named by their label (`stars-1.svg`, `stars-62.2k.svg`) rather
than by repo, so two repos on the same count share one file and a run that changes nothing writes
nothing. The trade-off is that a badge outlives the repo that needed it, which is why the writer
prunes `stars-*.svg` files no repo currently uses. Pruning is scoped to that one glob — nothing
else in `assets/` is ever touched.

### Why the badge SVG is taller than the badge

A star badge is an 18px capsule inside a 26px box. The extra 8px is transparent space below it.

HTML's `align="middle"` is not CSS `vertical-align: middle`: it centres the image on the text
*baseline*, which left the capsule sitting 4px below the optical centre of the line. GitHub strips
author `style` attributes, so the offset cannot be corrected with CSS. Padding the SVG can, because
an image centred on the baseline is lifted by half of whatever transparent space hangs beneath it
— so 8px of padding raises the capsule by exactly the 4px needed.

The 4px figure was measured, not estimated: the block was rendered through GitHub's own
`POST /markdown` API, loaded in a headless browser, and the capsule centre compared against the ink
centre of the description text. Padding of 0/4/8/10/12 produced offsets of 4/2/0/-1/-2 px. The cost
is about 4px of extra line height on rows that have a badge.

### Why the star sits off-centre in the path data

Inside the badge, the star and the number are aligned on one line at y=9, and getting there needed
two corrections.

The star's path is built around cy=9.477, not 9. A five-point star's *ink* is not symmetric about
its geometric centre — the single top point reaches further than the two bottom ones — so centring
the geometry left the star about 1px above the digits. The path is generated from the ink bounds
instead.

The number is drawn at baseline y=12.5 with `textLength` pinned and
`lengthAdjust="spacingAndGlyphs"`. Digit cap ascent is 7.0 at font-size 11, so that baseline puts
the cap centre on y=9 too. Pinning `textLength` matters because the badge renders in whatever font
the reader has: without it, the star-to-number gap drifted with the label (4.69px on `999`, 7.90px
on `11.1k`), since the text was centred inside a width that was only estimated. Advance widths are
measured per glyph — digits are not one width, `1` is 3.85 and `0` is 6.04 — and a flat average was
what made the wide labels lopsided.

The result holds across every label: star ink centre and digit cap centre both at y=9, a constant
5.0px gap between them, and 6.24px of padding on each side. `TestBadgeAlignment` pins all of it,
because none of it is visible in the markup.

### Why there is no separator glyph

Name, badge and description are separated by open space (`&ensp;&nbsp;`), not by punctuation. A
colon read as a label when it followed a badge image, and it attached to different things depending
on whether a repo had stars. Plain spaces collapse in HTML, so the air comes from entities.

## Known limits

- Up to 100 repos. Pagination is a documented TODO in `github_client.py` — switch to the `Link` header pattern when that limit is hit.
- Single marker pair. If sections need to live in different parts of the README, split into multiple marker pairs (a small change to `readme_writer.py` + `main.py`).
