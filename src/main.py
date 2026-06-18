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
    parser.add_argument(
        "--feature-repo",
        action="append",
        metavar="OWNER/NAME",
        help="Also feature a repo from another owner/org (repeatable), e.g. wendhq/wend.",
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

    own = stats.filter_active(github_client.fetch_user_repos(owner, token))
    repo_count = stats.count_repos(own)
    languages = stats.top_languages(own)

    extra = [github_client.fetch_repo(name, token) for name in (args.feature_repo or [])]
    featured = stats.most_recent_first(stats.dedupe(github_client.filter_featured(own) + extra))

    block = renderer.compose(featured, repo_count, languages)
    full_block = renderer.wrap_with_markers(block)

    if args.dry_run:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
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
