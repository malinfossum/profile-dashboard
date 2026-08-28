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

## Known limits

- Up to 100 repos. Pagination is a documented TODO in `github_client.py` — switch to the `Link` header pattern when that limit is hit.
- Single marker pair. If sections need to live in different parts of the README, split into multiple marker pairs (a small change to `readme_writer.py` + `main.py`).
