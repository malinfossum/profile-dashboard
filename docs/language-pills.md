# Spec — language pills from per-repo breakdowns

Status: implemented, 2026-08-28. Supersedes the primary-language ranking in `stats.top_languages`.

## Problem

The stats line ranks languages by GitHub's **primary language** field — one label per repo,
assigned by dominant bytes. That field hides most of what the work actually is:

| Repo | Primary language | What it also contains |
|---|---|---|
| `varde` | C# | 74,906 bytes of TypeScript |
| `hugin` | C# | 222,849 bytes of TypeScript |
| `workbench` | CSS | 100,882 JavaScript, 18,626 C#, 4,921 TypeScript |

TypeScript is 302,676 bytes across `varde`, `hugin` and `workbench` and cannot appear in the
pills at all, because it is not the primary label of any repo. The profile reads as
backend-only when the work is not.

## Finding that shapes the design

**Switching to `/languages` does not on its own put TypeScript in the pills.** Measured across
the 12 active repos that report any language, at three plausible rankings:

| Rank | A. total bytes | B. repos containing it | C. summed share-of-repo |
|---|---|---|---|
| 1 | C# 1,620,090 | CSS 9 | C# 4.03 |
| 2 | JavaScript 743,529 | JavaScript 9 | JavaScript 3.80 |
| 3 | CSS 394,900 | HTML 8 | CSS 1.39 |
| 4 | **TypeScript 304,545** | C# 7 | Python 1.10 |
| 5 | HTML 65,542 | **TypeScript 4** | HTML 0.97 |
| 6 | Python 34,977 | PowerShell 2 | **TypeScript 0.54** |

TypeScript is 4th, 5th and 6th respectively. Ranking method alone never solves this.
Method B promotes HTML into the top three. Method C brings Python back — the exact thing
we removed today.

So ranking by total bytes (A) is necessary but not sufficient — with three pills it still
yields `C# · JavaScript · CSS`.

**Decision: rank by total bytes, exclude CSS and HTML, keep three pills.** That yields
`C# · JavaScript · TypeScript` — a tighter engineering signal, which is the point of the
line. Markup and styling are real work but they are not the signal a profile visitor is
reading this line for.

The alternative considered was four pills including CSS (`C# · JavaScript · CSS · TypeScript`),
which keeps everything and drops nothing. Rejected in favour of the tighter three.

## Design

Follows the existing discipline: new fetcher, new aggregator, one wire-up. Nothing rewrites.

### `github_client.fetch_repo_languages(full_name, token) -> dict[str, int]`

`GET /repos/{full_name}/languages`. Returns `{language: bytes}`, `{}` for a repo with no
detected language (`getacademy` and `malinfossum` both return `{}` today).

Network failure on a single repo must not fail the run — return `{}` and let the caller
carry on. A dropped repo shifts byte totals slightly; a crashed workflow leaves the profile
stale, which is worse. Log the skip to stderr so it is visible in the run log.

### `stats.total_language_bytes(breakdowns, exclude) -> Counter`

Pure. Sums a list of `{language: bytes}` dicts into one counter, dropping excluded languages
case-insensitively. No I/O, no formatting.

### `stats.top_languages` — rewritten signature

```python
def top_languages(byte_counts: Counter, n: int = 3) -> list[str]
```

Takes a byte counter instead of a repo list. Keeps today's alphabetical tie-break so the line
stays stable between runs. Exclusion moves up into `total_language_bytes`, so ranking has one
job. The repo-list version is deleted, not kept alongside — two ranking paths would drift.

### `main.py` wire-up

After `own = stats.filter_active(...)`, fetch a breakdown per repo, sum, rank. One extra call
per active repo — **14 today**, against a 5,000/hour authenticated limit. Not a concern at
this size, but it makes the existing pagination TODO in `github_client.py` more relevant:
past ~100 repos both the repo list and this loop need attention together.

No renderer change. `render_stats_line` already takes `languages: list[str]` and does not care
how long the list is.

## CLI

`--exclude-language` keeps working and now applies to byte totals. The workflow passes
`Python`, `CSS` and `HTML`. Python is redundant at this ranking — it falls to 6th on bytes —
but it stays explicit rather than relying on the ranking to keep it out.

`--language-count N` (default 3) makes the pill count tunable without a code change, so
revisiting the three-versus-four call later is a workflow edit.

## Tests

Written first, per the repo's existing practice. Against `tests/test_stats.py`:

- sums bytes across multiple repo breakdowns
- ignores repos reporting `{}`
- excludes named languages case-insensitively
- breaks count ties alphabetically (port the existing test to the new signature)
- respects `n`
- empty input returns `[]`

And in `tests/test_github_client.py` (new file — the module has no tests today):

- parses a `/languages` response into a dict
- returns `{}` and does not raise when the request fails

Existing renderer tests are unaffected.

## Result

Live as of 2026-08-28: `C# · JavaScript · TypeScript`.

## Known limits

- Byte counts favour verbose languages and generated or vendored files. C# leads partly
  because C# is wordy. This is a proxy for breadth, not a measure of skill.
- `/languages` reflects the default branch only.
- Private repos stay invisible — the PAT is scoped to the profile repo, and the repo list
  call is public-only by design.
