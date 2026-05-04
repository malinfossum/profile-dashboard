"""GitHub API client. Network is contained to this module."""

from __future__ import annotations

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


def filter_featured(repos: list[dict]) -> list[dict]:
    return [r for r in repos if FEATURED_TOPIC in (r.get("topics") or [])]
