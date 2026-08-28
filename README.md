# profile-dashboard

A small Python tool that generates a live dashboard section inside my GitHub profile README. Runs daily on GitHub Actions.

## What it shows

- **Featured projects** — repos I tag with the `featured` topic, plus any passed via `--feature-repo` (e.g. a collaboration in another org), sorted by last-pushed.
- **Stats** — count of original projects (forks and archived repos excluded), top languages by
  bytes written across all repos, and the last-updated date (UTC).
- **Upstream contributions** — merged PRs authored in repos owned by others, grouped by repo,
  with a generated count pill (`--pill-path`).

The output is written between two HTML comment markers in `malinfossum/README.md`. It only commits when the rendered block actually changes, so the profile repo stays quiet.

## Stack

- Python 3.12+
- `requests` — HTTP only
- `pytest` — tests
- `ruff` — lint + format
- GitHub Actions — daily cron

## Architecture

Five files, each with one job:

| File | Responsibility |
|---|---|
| `src/github_client.py` | Talks to the GitHub API. Returns plain dicts. |
| `src/stats.py` | Pure aggregation. Counts repos, sums language bytes and ranks them, groups featured repos. Filters forks and archived repos. |
| `src/renderer.py` | Composes Markdown sections. Escapes user-supplied strings. |
| `src/readme_writer.py` | Replaces content between markers in the target README. Idempotent. |
| `src/main.py` | Top-down orchestrator. Wires everything together. |

The discipline that keeps it maintainable: **the renderer never calls the API, and stats never format strings.** New features add new functions; nothing existing gets rewritten.

## First-time setup

1. **Create a fine-grained personal access token** at <https://github.com/settings/personal-access-tokens/new>:
   - Resource owner: your account
   - Repository access: *Only select repositories* → pick `malinfossum/malinfossum`
   - Permissions: *Repository permissions* → *Contents* → *Read and write*. Nothing else.
   - Expiration: 1 year (small blast radius, less rotation churn)
2. **Add the token as a repo secret** in `profile-dashboard`:
   - Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `PROFILE_README_TOKEN`
3. **Add the markers** to `malinfossum/README.md` where the dashboard should appear:
   ```html
   <!-- DASHBOARD:START -->
   <!-- DASHBOARD:END -->
   ```
4. **Tag at least one repo** with the `featured` topic on GitHub (Repo page → About gear → Topics).
5. **Trigger the workflow manually** once: Actions → *Update dashboard* → *Run workflow*.
6. **Set a calendar reminder ~1 month before expiry** to rotate the token.

## Local development

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows (Git Bash)
# .venv\Scripts\Activate.ps1    # Windows (PowerShell)
# source .venv/bin/activate     # macOS / Linux

pip install -e ".[dev]"
```

### Run

```bash
# Dry run — prints the generated block, writes nothing
python -m src.main --repo malinfossum/malinfossum --dry-run

# Real run against a local README
python -m src.main --repo malinfossum/malinfossum --readme-path ./path/to/README.md

# Also feature a repo from another org (repeatable)
python -m src.main --repo malinfossum/malinfossum --readme-path ./path/to/README.md \
  --feature-repo wendhq/wend
```

Other flags: `--group KEY=NAME,NAME` assigns featured repos to a purpose group,
`--exclude-owner OWNER` keeps an org's repos out of the upstream-contributions count,
`--exclude-language LANGUAGE` keeps a language out of the stats pills, and
`--language-count N` sets how many pills to show (default 3). All are repeatable
except `--language-count`.

A token is required for both. Set it locally as the env var `PROFILE_README_TOKEN` (do not commit it).

### Tests and lint

```bash
ruff check
ruff format --check
pytest
```

## Token rotation

1. Create a new fine-grained PAT with the same scope and permission as before.
2. Update the `PROFILE_README_TOKEN` secret in this repo.
3. Manually trigger *Update dashboard*; confirm it succeeds.
4. Revoke the old token at <https://github.com/settings/personal-access-tokens>.

## License

Apache 2.0 — see [LICENSE](LICENSE).
