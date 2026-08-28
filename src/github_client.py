"""GitHub API client. Network is contained to this module."""

from __future__ import annotations

import sys

import requests

API_ROOT = "https://api.github.com"
FEATURED_TOPIC = "featured"
# v1 fetches up to 100 repos in a single page. To support more, switch to the
# paginated `Link` header pattern here. Nothing else needs to change.
PAGE_SIZE = 100


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "profile-dashboard",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_user_repos(username: str, token: str) -> list[dict]:
    url = f"{API_ROOT}/users/{username}/repos"
    params = {"per_page": PAGE_SIZE, "sort": "pushed", "type": "owner"}
    response = requests.get(url, headers=_headers(token), params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_repo(full_name: str, token: str) -> dict:
    """Fetch a single repo by 'owner/name' — lets us feature repos in other orgs."""
    url = f"{API_ROOT}/repos/{full_name}"
    response = requests.get(url, headers=_headers(token), timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_repo_languages(full_name: str, token: str) -> dict[str, int]:
    """Byte count per language for one repo, default branch only.

    A repo that fails to fetch returns {} rather than raising: one unreachable
    repo skews the totals slightly, but a crashed run leaves the profile stale.
    """
    url = f"{API_ROOT}/repos/{full_name}/languages"
    try:
        response = requests.get(url, headers=_headers(token), timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"warning: could not fetch languages for {full_name}: {exc}", file=sys.stderr)
        return {}


def filter_featured(repos: list[dict]) -> list[dict]:
    return [r for r in repos if FEATURED_TOPIC in (r.get("topics") or [])]


def fetch_merged_upstream_prs(username: str, token: str, exclude_owners: list[str]) -> list[dict]:
    """Merged PRs authored by the user in repos owned by others."""
    owners = {username, *exclude_owners}
    q = f"is:pr is:merged author:{username} " + " ".join(f"-user:{o}" for o in sorted(owners))
    url = f"{API_ROOT}/search/issues"
    params = {"q": q, "per_page": PAGE_SIZE, "sort": "created", "order": "asc"}
    response = requests.get(url, headers=_headers(token), params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("items", [])
