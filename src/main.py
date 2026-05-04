"""Entrypoint. Wires fetch → filter → aggregate → render → write."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src import github_client, renderer, stats
from src.readme_writer import MarkersMissingError, write_block


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the profile dashboard block.")
    parser.add_argument(
        "--repo",
        required=True,
        help="Target repo as 'owner/name' (e.g., malinfossum/malinfossum).",
    )
    parser.add_argument(
        "--readme-path",
        type=Path,
        help="Path to the target README. Required unless --dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rendered block to stdout; do not modify any file.",
    )
    return parser.parse_args(argv)


def _require_token() -> str:
    token = os.environ.get("PROFILE_README_TOKEN")
    if not token:
        print("error: PROFILE_README_TOKEN env var is not set.", file=sys.stderr)
        sys.exit(2)
    return token


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.dry_run and args.readme_path is None:
        print("error: --readme-path is required unless --dry-run is set.", file=sys.stderr)
        return 2

    owner = args.repo.split("/", 1)[0]
    token = _require_token()

    repos = github_client.fetch_user_repos(owner, token)
    active = stats.filter_active(repos)
    featured = github_client.filter_featured(active)
    repo_count = stats.count_repos(active)
    languages = stats.top_languages(active)

    block = renderer.compose(featured, repo_count, languages)
    full_block = renderer.wrap_with_markers(block)

    if args.dry_run:
        print(full_block)
        return 0

    try:
        changed = write_block(args.readme_path, full_block)
    except MarkersMissingError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print("dashboard updated" if changed else "no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
