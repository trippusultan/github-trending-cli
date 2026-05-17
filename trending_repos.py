"""
trending-repos — GitHub Trending CLI

Fetches trending GitHub repositories via the GitHub Search API and
displays them in a clean, column-aligned table sorted by star count.

Usage:
    trending-repos [--duration {day,week,month,year}] [--limit N]

Requirements:
    pip install -r requirements.txt

Example:
    trending-repos --duration month --limit 20
    trending-repos                  # defaults: week, 10
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from rich.console import Console

API_URL   = "https://api.github.com/search/repositories"
MIN_STARS = 50                        # only repos with >= this many stars
PER_PAGE  = 100                       # GitHub search API cap per request

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="trending-repos",
        description="Show trending GitHub repositories by star count over a time range.",
    )
    parser.add_argument(
        "--duration",
        choices=["day", "week", "month", "year"],
        default="week",
        help="Time window for trending repos (default: week).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of repos to display (default: 10).",
    )
    return parser.parse_args()


def since_iso(duration: str) -> str:
    """Return an ISO-8601 UTC timestamp for the start of the duration window."""
    now = datetime.now(timezone.utc)
    delta_map = {
        "day":   timedelta(days=1),
        "week":  timedelta(weeks=1),
        "month": timedelta(days=30),
        "year":  timedelta(days=365),
    }
    return (now - delta_map[duration]).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_query(duration: str) -> str:
    return f"pushed:>={since_iso(duration)} stars:>={MIN_STARS}"


def fetch_repos(query: str, limit: int) -> list[dict[str, Any]]:
    params: dict = {
        "q":        query,
        "sort":     "stars",
        "order":    "desc",
        "per_page": min(limit, PER_PAGE),
    }
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "trending-repos-cli",
    }

    try:
        resp = requests.get(API_URL, params=params, headers=headers, timeout=15)
    except requests.exceptions.Timeout:
        print("Error: GitHub API request timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        print(f"Error: Network error — {exc}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code == 403:
        print("Error: GitHub API rate limit exceeded.", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 422:
        print("Error: Invalid search query.", file=sys.stderr)
        sys.exit(1)
    if resp.status_code != 200:
        print(
            f"Error: GitHub API returned {resp.status_code} — {resp.text[:200]}",
            file=sys.stderr,
        )
        sys.exit(1)

    return resp.json().get("items", [])[:limit]


# ── column widths ────────────────────────────────────────────────────────

W_INDEX  = 3
W_REPO   = 28
W_LANG   = 12
W_STARS  = 7
W_SEP    = 3
W_DESC   = 50
W_URL    = 0   # filled dynamically from terminal width

SEP = "  "    # two spaces between columns


def _url_w(tw: int) -> int:
    return max(tw - (W_INDEX + W_SEP + W_REPO + W_SEP + W_LANG + W_SEP + W_STARS + W_SEP + W_DESC), 20)


def _header(duration: str, tw: int) -> str:
    uw   = _url_w(tw)
    head = f"{'#':>{W_INDEX}}{SEP}{'Repository':<{W_REPO}}{SEP}{'Language':<{W_LANG}}{SEP}{'Stars':>{W_STARS}}{SEP}{'Description':<{W_DESC}}{SEP}URL"
    line = "═" * len(head)
    return f"\n{line}\n  Trending Repos · {duration}\n{line}"


def _row(
    idx: int,
    repo: dict[str, Any],
    tw: int,
) -> str:
    repo_name = repo.get("full_name", "?")
    lang      = repo.get("language") or "—"
    stars     = repo.get("stargazers_count", 0)
    desc      = (repo.get("description") or "").strip()
    if len(desc) > W_DESC:
        desc = desc[: W_DESC - 1] + "…"
    url       = repo.get("html_url", "")
    uw        = _url_w(tw)
    return (
        f"{idx:>{W_INDEX}}{SEP}"
        f"{repo_name:<{W_REPO}}{SEP}"
        f"{lang:<{W_LANG}}{SEP}"
        f"{f'{stars:,}':>{W_STARS}}{SEP}"
        f"{desc:<{W_DESC}}{SEP}"
        f"{url:<{uw}}"
    )


def display(repos: list[dict[str, Any]], duration: str) -> None:
    tw = console.width
    console.print(_header(duration, tw))
    for idx, repo in enumerate(repos, 1):
        console.print(_row(idx, repo, tw))
    console.print(
        f"\n[dim]Fetched {len(repos)} repos  |  "
        f"Source: GitHub Search API  |  "
        f"Min stars: {MIN_STARS}[/dim]\n"
    )


def main() -> None:
    args  = parse_args()
    limit = max(args.limit, 1)
    query = build_query(args.duration)
    repos = fetch_repos(query, limit)

    if not repos:
        print(f"No trending repositories found in the last {args.duration}.")
        sys.exit(0)

    display(repos, args.duration)


if __name__ == "__main__":
    main()
