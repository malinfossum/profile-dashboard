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
