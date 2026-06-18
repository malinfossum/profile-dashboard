"""Pure aggregation. No I/O, no formatting."""

from __future__ import annotations

from collections import Counter


def filter_active(repos: list[dict]) -> list[dict]:
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def count_repos(repos: list[dict]) -> int:
    return len(repos)


def top_languages(repos: list[dict], n: int = 3) -> list[str]:
    counter = Counter(r["language"] for r in repos if r.get("language"))
    return [lang for lang, _ in counter.most_common(n)]


def most_recent_first(repos: list[dict]) -> list[dict]:
    """Sort by last-pushed, newest first. ISO timestamps sort lexically."""
    return sorted(repos, key=lambda r: r.get("pushed_at") or "", reverse=True)


def dedupe(repos: list[dict]) -> list[dict]:
    """Drop repos with a repeated id, keeping the first occurrence."""
    seen = set()
    result = []
    for repo in repos:
        key = repo.get("id")
        if key in seen:
            continue
        seen.add(key)
        result.append(repo)
    return result
