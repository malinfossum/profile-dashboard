"""Entrypoint. Wires fetch → filter → aggregate → render → write."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src import github_client, renderer, stats
from src.readme_writer import MarkersMissingError, write_block, write_text_file


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
    parser.add_argument(
        "--group",
        action="append",
        metavar="KEY=NAME,NAME",
        help="Assign featured repos to a purpose group (repeatable, ordered), "
        "e.g. focus=tidsro,ignite. Keys: focus, wellbeing, momentum.",
    )
    parser.add_argument(
        "--exclude-owner",
        action="append",
        metavar="OWNER",
        help="Owner/org whose repos never count as upstream contributions "
        "(repeatable), e.g. wendhq. The profile owner is always excluded.",
    )
    parser.add_argument(
        "--exclude-language",
        action="append",
        metavar="LANGUAGE",
        help="Language that never earns a pill in the stats line (repeatable, "
        "case-insensitive), e.g. CSS.",
    )
    parser.add_argument(
        "--language-count",
        type=int,
        default=3,
        metavar="N",
        help="How many language pills to show in the stats line (default 3).",
    )
    parser.add_argument(
        "--pill-path",
        type=Path,
        help="Path to write the merged-PRs pill SVG (assets/oss-merged.svg in the "
        "target repo checkout). Skipped when omitted.",
    )
    return parser.parse_args(argv)


def _parse_group_specs(raw: list[str] | None) -> list[tuple[str, list[str]]]:
    specs = []
    for entry in raw or []:
        key, _, names = entry.partition("=")
        if key not in renderer.GROUPS or not names:
            keys = ", ".join(renderer.GROUPS)
            print(f"error: bad --group '{entry}' (keys: {keys}).", file=sys.stderr)
            sys.exit(2)
        specs.append((key, [n.strip() for n in names.split(",") if n.strip()]))
    return specs


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
    breakdowns = [github_client.fetch_repo_languages(r["full_name"], token) for r in own]
    languages = stats.top_languages(
        stats.total_language_bytes(breakdowns, exclude=args.exclude_language or []),
        n=args.language_count,
    )

    extra = [github_client.fetch_repo(name, token) for name in (args.feature_repo or [])]
    featured = stats.most_recent_first(stats.dedupe(github_client.filter_featured(own) + extra))

    grouped, leftovers = stats.group_featured(featured, _parse_group_specs(args.group))
    for repo in leftovers:
        full_name = repo.get("full_name")
        print(f"warning: featured repo '{full_name}' is in no --group; skipped.", file=sys.stderr)

    pr_items = github_client.fetch_merged_upstream_prs(owner, token, args.exclude_owner or [])
    by_repo = stats.group_prs_by_repo(pr_items)
    contrib_repos = []
    for full_name, prs in by_repo.items():
        upstream = github_client.fetch_repo(full_name, token)
        contrib_repos.append(
            {
                "full_name": full_name,
                "html_url": upstream.get("html_url", ""),
                "stargazers_count": upstream.get("stargazers_count") or 0,
                "prs": prs,
            }
        )
    contrib_repos.sort(key=lambda r: r["stargazers_count"], reverse=True)
    pr_count = len(pr_items)

    block = renderer.compose(grouped, contrib_repos, pr_count, repo_count, languages)
    full_block = renderer.wrap_with_markers(block)
    pill_svg = renderer.render_oss_pill_svg(pr_count)

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
    if args.pill_path is not None:
        pill_changed = write_text_file(args.pill_path, pill_svg)
        changed = changed or pill_changed
    print("dashboard updated" if changed else "no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
