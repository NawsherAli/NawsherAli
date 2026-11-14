#!/usr/bin/env python3
"""Fetch real, public GitHub statistics for the profile and store them in
data/github-stats.json.

Design rules
  * Standard library only.
  * Never invent numbers: every value comes from the GitHub REST/GraphQL API.
  * On any failure, keep the previous file untouched (exit code 0 with a warning,
    or 1 with --strict) so the profile keeps rendering the last good data.
  * Deterministic output: the file only changes when the underlying data changes.
    "as_of" is updated only when metrics differ from the stored ones.

Usage
  GITHUB_TOKEN=... python3 scripts/fetch_github_stats.py [--login NawsherAli] [--strict]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "profile.toml"
OUT = ROOT / "data" / "github-stats.json"
API = "https://api.github.com"
SCHEMA = 1
MIN_RATE_REMAINING = 20


class FetchError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[fetch] {msg}", flush=True)


class GitHubClient:
    """Tiny REST/GraphQL client with retries and rate-limit protection."""

    def __init__(self, token: str | None, retries: int = 2, timeout: int = 20):
        self.token = token
        self.retries = retries
        self.timeout = timeout

    def _request(self, url: str, data: bytes | None = None) -> dict | list:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "nawsherali-profile-bot",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if data is not None:
            headers["Content-Type"] = "application/json"
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    remaining = r.headers.get("X-RateLimit-Remaining")
                    if remaining is not None and int(remaining) < MIN_RATE_REMAINING:
                        raise FetchError(f"rate limit nearly exhausted ({remaining} left); aborting")
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last = e
                if e.code in (401, 403, 404, 422):
                    raise FetchError(f"{e.code} for {url}") from e
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                last = e
            if attempt < self.retries:
                time.sleep(2 ** attempt)
        raise FetchError(f"request failed after retries: {url} ({last})")

    def rest(self, path: str):
        return self._request(f"{API}{path}")

    def graphql(self, query: str, variables: dict):
        body = json.dumps({"query": query, "variables": variables}).encode()
        res = self._request(f"{API}/graphql", data=body)
        if not isinstance(res, dict) or res.get("errors"):
            raise FetchError(f"graphql error: {res.get('errors') if isinstance(res, dict) else res}")
        return res["data"]


CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def _date(s: str | None) -> str | None:
    return s[:10] if s else None


def collect(client: GitHubClient, login: str, exclude: list[str]) -> dict:
    """Return a validated metrics dict (without as_of/status)."""
    user = client.rest(f"/users/{login}")
    if not isinstance(user, dict) or user.get("login", "").lower() != login.lower():
        raise FetchError("unexpected /users response")

    repos = client.rest(f"/users/{login}/repos?per_page=100&type=owner&sort=full_name")
    if not isinstance(repos, list):
        raise FetchError("unexpected /repos response")
    own = [r for r in repos if not r.get("fork") and not r.get("private")]
    excl = {e.lower() for e in exclude}

    repo_rows, languages = [], {}
    for r in sorted(own, key=lambda r: r["name"].lower()):
        hidden = r["name"].lower() in excl
        repo_rows.append({
            "name": r["name"],
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "stars": int(r.get("stargazers_count", 0)),
            "forks": int(r.get("forks_count", 0)),
            "pushed": _date(r.get("pushed_at")),
            "url": r.get("html_url", ""),
            "archived": bool(r.get("archived")),
            "excluded": hidden,
        })
        if not hidden and not r.get("archived"):
            langs = client.rest(f"/repos/{login}/{r['name']}/languages")
            if isinstance(langs, dict):
                for k, v in langs.items():
                    languages[k] = languages.get(k, 0) + int(v)

    contributions = None
    if client.token:
        try:
            data = client.graphql(CONTRIB_QUERY, {"login": login})
            weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
            contributions = normalise_calendar(weeks)
        except (FetchError, KeyError, TypeError) as e:
            log(f"contributions unavailable: {e}")
    else:
        log("no token: skipping contribution calendar (GraphQL needs auth)")

    visible = [r for r in repo_rows if not r["excluded"]]
    metrics = {
        "login": user["login"],
        "name": user.get("name") or user["login"],
        "created": _date(user.get("created_at")),
        "public_repos": int(user.get("public_repos", 0)),
        "followers": int(user.get("followers", 0)),
        "total_stars": sum(r["stars"] for r in repo_rows),
        "last_push": max((r["pushed"] for r in visible if r["pushed"]), default=None),
        "languages": dict(sorted(languages.items(), key=lambda kv: (-kv[1], kv[0]))),
        "repos": repo_rows,
        "contributions": contributions,
    }
    validate(metrics)
    return metrics


def normalise_calendar(weeks: list) -> dict:
    """Keep the last 52 *complete* weeks (Sun–Sat) so the data only shifts weekly."""
    full = [w["contributionDays"] for w in weeks if len(w.get("contributionDays", [])) == 7]
    full = full[-52:]
    grid = [[int(d["contributionCount"]) for d in w] for w in full]
    return {
        "start": full[0][0]["date"] if full else None,
        "end": full[-1][-1]["date"] if full else None,
        "total": sum(map(sum, grid)),
        "weeks": grid,
    }


def validate(m: dict) -> None:
    for k in ("public_repos", "followers", "total_stars"):
        if not isinstance(m[k], int) or m[k] < 0:
            raise FetchError(f"invalid metric {k}={m[k]!r}")
    if m["contributions"]:
        c = m["contributions"]
        if any(v < 0 for w in c["weeks"] for v in w) or c["total"] < 0:
            raise FetchError("invalid contribution data")


def merge(previous: dict | None, metrics: dict, today: str) -> dict:
    """Keep as_of stable when nothing changed (no needless commits)."""
    prev_metrics = (previous or {}).get("metrics")
    as_of = previous.get("as_of") if previous and prev_metrics == metrics else today
    return {"schema": SCHEMA, "status": "ok", "as_of": as_of, "metrics": metrics}


def mark_stale(previous: dict | None, today: str, stale_after: int) -> dict | None:
    if not previous or previous.get("status") == "pending":
        return previous
    as_of = dt.date.fromisoformat(previous["as_of"])
    if (dt.date.fromisoformat(today) - as_of).days > stale_after and previous.get("status") != "stale":
        return {**previous, "status": "stale"}
    return previous


def write_json(path: Path, data: dict) -> bool:
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--login")
    ap.add_argument("--strict", action="store_true", help="exit 1 on fetch failure")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    login = args.login or cfg["identity"]["handle"]
    tele = cfg.get("telemetry", {})
    out = Path(args.out)
    previous = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    client = GitHubClient(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    try:
        metrics = collect(client, login, tele.get("exclude_repos", []))
    except FetchError as e:
        log(f"WARNING: fetch failed, keeping previous data: {e}")
        stale = mark_stale(previous, today, int(tele.get("stale_after_days", 3)))
        if stale is not None and stale is not previous:
            write_json(out, stale)
            log("previous data marked as stale")
        return 1 if args.strict else 0

    changed = write_json(out, merge(previous, metrics, today))
    log(f"{'updated' if changed else 'unchanged'}: repos={metrics['public_repos']} "
        f"followers={metrics['followers']} stars={metrics['total_stars']} "
        f"contrib={(metrics['contributions'] or {}).get('total')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
