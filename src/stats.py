"""Pure aggregation. No I/O, no formatting."""

from __future__ import annotations

from collections import Counter


def filter_active(repos: list[dict]) -> list[dict]:
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def count_repos(repos: list[dict]) -> int:
    return len(repos)


def total_language_bytes(
    breakdowns: list[dict[str, int]], exclude: list[str] | None = None
) -> Counter:
    """Sum per-repo {language: bytes} maps into one counter."""
    skip = {lang.casefold() for lang in exclude or []}
    totals: Counter = Counter()
    for breakdown in breakdowns:
        for lang, byte_count in breakdown.items():
            if lang.casefold() not in skip:
                totals[lang] += byte_count
    return totals


def top_languages(byte_counts: Counter, n: int = 3) -> list[str]:
    """Top n languages by total bytes.

    Ties break alphabetically so the pill is stable between runs — Counter alone
    falls back to insertion order, which follows whatever order the API replied in.
    """
    ranked = sorted(byte_counts.items(), key=lambda item: (-item[1], item[0]))
    return [lang for lang, _ in ranked[:n]]


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


def group_featured(
    featured: list[dict], group_specs: list[tuple[str, list[str]]]
) -> tuple[list[tuple[str, list[dict]]], list[dict]]:
    """Split featured repos into named groups per the CLI specs.

    Each spec is (group_key, [repo names or owner/name]). Within a group, repos
    keep spec order. Returns (grouped, leftovers) — leftovers are featured repos
    no spec claimed, so the caller can warn instead of dropping them silently.
    """
    by_name: dict[str, dict] = {}
    for repo in featured:
        by_name[repo.get("name", "")] = repo
        by_name[repo.get("full_name", "")] = repo
    claimed_ids = set()
    grouped = []
    for key, names in group_specs:
        members = []
        for name in names:
            repo = by_name.get(name)
            if repo is not None:
                members.append(repo)
                claimed_ids.add(repo.get("id"))
        grouped.append((key, members))
    leftovers = [r for r in featured if r.get("id") not in claimed_ids]
    return grouped, leftovers


def group_prs_by_repo(items: list[dict]) -> dict[str, list[dict]]:
    """Group merged-PR search items by upstream repo full name."""
    by_repo: dict[str, list[dict]] = {}
    for item in items:
        full_name = item["repository_url"].split("/repos/", 1)[1]
        by_repo.setdefault(full_name, []).append(item)
    return by_repo
