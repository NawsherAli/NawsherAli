# Architecture

```
data/profile.toml ──┐                              ┌─► assets/generated/{dark,light}/*.svg
                    ├─► generate_profile_svgs.py ──┤
data/github-stats.json ┘        ▲                  └─► README.md
        ▲                       │
        │                    svgkit.py (design system)
fetch_github_stats.py ◄── GitHub REST + GraphQL (GITHUB_TOKEN)

validate_assets.py → XML, accessibility, forbidden content, README paths and anchors, secrets
tests/ → unit tests with synthetic API data (no network)
.github/workflows/update-profile.yml → tests → fetch → generate → validate → commit-if-changed
```

## Data flow and guarantees
| Concern | How it's handled |
|---|---|
| Real data only | Every live number comes from `/users/{login}`, `/users/{login}/repos`, `/repos/{o}/{r}/languages` or GraphQL `contributionCalendar`. CV facts are labelled "source: CV". Before the first sync the card says AWAITING FIRST SYNC instead of showing numbers |
| Forks | Never counted (stars, languages) |
| Excluded repos | `telemetry.exclude_repos`: still counted in public repos (that figure comes from GitHub), but never featured or used for languages |
| Rate limits | Aborts when `X-RateLimit-Remaining < 20`. About 3 + N calls per run |
| Failures | 2 retries with backoff. On failure the previous JSON is kept and the job continues. Data older than `stale_after_days` is marked STALE in the card |
| Validation | Non-negative integers, calendar sanity, user login match |
| Determinism | Sorted keys and lists, no timestamps. `as_of` only moves when metrics change. The calendar is trimmed to 52 complete weeks, so it shifts weekly, not daily |
| No empty commits | The workflow commits only when `git diff` is non-empty. Commits made with `GITHUB_TOKEN` don't retrigger workflows; `[skip ci]` is added too |
| Permissions | `contents: write` only. No personal access token needed |
| Secrets | None stored. The validator scans for token and key patterns |

## Thresholds
`show_stars_min`, `show_followers_min` and `show_contributions_min` keep vanity numbers off the profile until they mean something. Once contributions pass the threshold, the ACTIVITY LOG section (heatmap) and its nav link appear automatically and sections renumber.
