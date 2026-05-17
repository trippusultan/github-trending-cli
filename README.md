**[Project URL](https://roadmap.sh/projects/github-trending-cli)**

GitHub Trending CLI — a command-line tool that fetches and displays trending GitHub repositories sorted by star count. No authentication required for public data.

---

## Features

- **Time-range filtering** — `--duration` accepts `day`, `week`, `month`, `year`
- **Limit output** — `--limit N` (default 10)
- **Min star filter** — only repos with ≥ 50 stars are shown
- **Rich-formatted table** — repo name, language, stars ⭐, description, URL
- **Zero auth** — GitHub public API, no token required
- **Robust error handling** — timeout, rate-limit (403), bad status codes

---

## Install

```bash
# system-wide (rec. via virtualenv)
pip install -r requirements.txt

# or, as an editable package (registers the `trending-repos` command)
pip install -e .
```

---

## Usage

```bash
# defaults: duration=week  limit=10
trending-repos

# show 20 repos from the last month
trending-repos --duration month --limit 20

# last 24 h only
trending-repos --duration day --limit 5

# top repos from the past year
trending-repos --duration year --limit 15
```

---

## CLI Args

| Flag | Values | Default | Purpose |
|---|---|---|---|
| `--duration` | `day` / `week` / `month` / `year` | `week` | Time window for the "pushed ≥" search filter |
| `--limit` | integer ≥ 1 | 10 | Max repos to display |

---

## Example Output

```
┏━━ Trending Repos · week ━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #  Repository             Language       Stars   Description                 URL                                              ┃
┃ 1  dottu/dotfiles          Python          ⭐ 1,234 My personal dotfiles…       https://github.com/dottu/dotfiles               ┃
...
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Fetched 10 repos · Source: GitHub Search API · Min stars: 50
```

---

## How it works

1. Calculates an ISO-8601 UTC timestamp for `now - <duration>`.
2. Calls `GET https://api.github.com/search/repositories` with:
   - `q=pushed:>={timestamp} stars:>=50`
   - `sort=stars&order=desc`
3. Parses the JSON, slices to `--limit`, and renders with **Rich**.

---

## Error Handling

| Situation | Exit |
|---|---|
| Network timeout | `1` — "request timed out" |
| Network error | `1` — "Network error: …" |
| HTTP 403 (rate-limited) | `1` — "rate limit exceeded" |
| HTTP 422 (bad query) | `1` — "Invalid search query" |
| No repos found | `0` — friendly empty-state message |
| `--limit < 1` | `3` (argparse error) |

---

MIT
