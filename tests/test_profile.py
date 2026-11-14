"""Tests for the profile generator and fetcher. Run: python3 -m unittest discover tests

All API data in these tests is SYNTHETIC test data, never shown on the profile.
"""
from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_github_stats as F  # noqa: E402
import generate_profile_svgs as G  # noqa: E402
import validate_assets as V  # noqa: E402


def synthetic_calendar(total_per_day: int, weeks: int = 54, partial_last: bool = True):
    out, day = [], 0
    for w in range(weeks):
        n = 3 if (partial_last and w == weeks - 1) else 7
        out.append({"contributionDays": [{"date": f"2026-{1 + (day + d) // 28 % 12:02d}-{1 + (day + d) % 28:02d}",
                                          "contributionCount": total_per_day} for d in range(n)]})
        day += n
    return out


class FakeClient:
    """Replays synthetic API responses."""

    def __init__(self, token="t", fail_on=None, contrib_per_day=1):
        self.token = token
        self.fail_on = fail_on
        self.contrib_per_day = contrib_per_day

    def rest(self, path):
        if self.fail_on and self.fail_on in path:
            raise F.FetchError("synthetic failure")
        if path.startswith("/users/") and path.count("/") == 2:
            return {"login": "NawsherAli", "name": "Nawsher Ali", "created_at": "2023-01-10T00:00:00Z",
                    "public_repos": 3, "followers": 7}
        if "/repos?" in path:
            return [
                {"name": "shredbottle", "fork": False, "private": False, "language": "Blade", "stargazers_count": 1,
                 "forks_count": 0, "pushed_at": "2024-07-28T00:00:00Z", "html_url": "u", "description": None},
                {"name": "tenancy-kit", "fork": False, "private": False, "language": "PHP", "stargazers_count": 4,
                 "forks_count": 1, "pushed_at": "2026-11-01T00:00:00Z", "html_url": "u", "description": "d"},
                {"name": "someone-elses", "fork": True, "private": False, "language": "Go", "stargazers_count": 99,
                 "forks_count": 0, "pushed_at": "2026-11-02T00:00:00Z", "html_url": "u"},
            ]
        if path.endswith("/languages"):
            return {"PHP": 9000, "Blade": 1000}
        raise AssertionError(path)

    def graphql(self, q, v):
        if self.fail_on == "graphql":
            raise F.FetchError("synthetic graphql failure")
        return {"user": {"contributionsCollection": {"contributionCalendar": {
            "weeks": synthetic_calendar(self.contrib_per_day)}}}}


def cfg():
    c, _ = G.load()
    return copy.deepcopy(c)


def stats_from(client, exclude=("shredbottle",)):
    m = F.collect(client, "NawsherAli", list(exclude))
    return F.merge(None, m, "2026-11-14")


class TestFetch(unittest.TestCase):
    def test_collect_excludes_forks_and_excluded_repos(self):
        m = F.collect(FakeClient(), "NawsherAli", ["shredbottle"])
        names = [r["name"] for r in m["repos"]]
        self.assertNotIn("someone-elses", names)                 # forks never counted
        self.assertEqual(m["total_stars"], 5)                     # 1 + 4, fork's 99 ignored
        self.assertEqual(m["languages"], {"PHP": 9000, "Blade": 1000})  # only tenancy-kit fetched
        self.assertEqual(m["last_push"], "2026-11-01")            # excluded repo ignored
        self.assertTrue(next(r for r in m["repos"] if r["name"] == "shredbottle")["excluded"])

    def test_calendar_keeps_52_complete_weeks(self):
        c = F.collect(FakeClient(contrib_per_day=2), "NawsherAli", [])["contributions"]
        self.assertEqual(len(c["weeks"]), 52)
        self.assertTrue(all(len(w) == 7 for w in c["weeks"]))
        self.assertEqual(c["total"], 52 * 7 * 2)

    def test_no_token_skips_contributions(self):
        self.assertIsNone(F.collect(FakeClient(token=None), "NawsherAli", [])["contributions"])

    def test_graphql_failure_is_non_fatal(self):
        self.assertIsNone(F.collect(FakeClient(fail_on="graphql"), "NawsherAli", [])["contributions"])

    def test_invalid_metric_rejected(self):
        m = F.collect(FakeClient(), "NawsherAli", [])
        m["followers"] = -1
        with self.assertRaises(F.FetchError):
            F.validate(m)

    def test_as_of_stable_when_unchanged(self):
        m = F.collect(FakeClient(), "NawsherAli", [])
        first = F.merge(None, m, "2026-11-01")
        again = F.merge(first, copy.deepcopy(m), "2026-11-14")
        self.assertEqual(again["as_of"], "2026-11-01")
        m2 = copy.deepcopy(m); m2["followers"] += 1
        self.assertEqual(F.merge(first, m2, "2026-11-14")["as_of"], "2026-11-14")

    def test_failure_keeps_previous_file_and_marks_stale(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "stats.json"
            prev = {"schema": 1, "status": "ok", "as_of": "2026-01-01", "metrics": {"x": 1}}
            out.write_text(json.dumps(prev))
            with mock.patch.object(F, "GitHubClient", lambda *a, **k: FakeClient(fail_on="/users/")):
                rc = F.main(["--out", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text())
            self.assertEqual(data["metrics"], {"x": 1})
            self.assertEqual(data["status"], "stale")
            with mock.patch.object(F, "GitHubClient", lambda *a, **k: FakeClient(fail_on="/users/")):
                self.assertEqual(F.main(["--out", str(out), "--strict"]), 1)

    def test_rate_limit_guard(self):
        class Resp(io.BytesIO):
            headers = {"X-RateLimit-Remaining": "3"}
            def __enter__(self): return self
            def __exit__(self, *a): return False
        with mock.patch("urllib.request.urlopen", return_value=Resp(b"{}")):
            with self.assertRaises(F.FetchError):
                F.GitHubClient("t", retries=0).rest("/users/x")

    def test_network_error_retries_then_fails(self):
        import urllib.error
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")) as m, \
             mock.patch("time.sleep"):
            with self.assertRaises(F.FetchError):
                F.GitHubClient(None, retries=2).rest("/users/x")
            self.assertEqual(m.call_count, 3)


class TestGenerate(unittest.TestCase):
    def test_deterministic(self):
        c = cfg()
        s = stats_from(FakeClient())
        self.assertEqual(G.build_assets(c, s), G.build_assets(c, s))
        self.assertEqual(G.build_readme(c, s), G.build_readme(c, s))

    def test_pending_shows_no_numbers(self):
        svg = G.telemetry(cfg(), {"status": "pending"}, G.THEMES["dark"], "t")
        self.assertIn("AWAITING FIRST SYNC", svg)
        self.assertNotIn("PUBLIC REPOS", svg)

    def test_thresholds_hide_vanity_metrics(self):
        c = cfg()
        s = stats_from(FakeClient())                     # 5 stars, 7 followers, 364 contributions
        svg = G.telemetry(c, s, G.THEMES["dark"], "t")
        self.assertIn("PUBLIC REPOS", svg)
        self.assertNotIn("STARS EARNED", svg)
        self.assertNotIn("FOLLOWERS", svg)
        c["telemetry"]["show_stars_min"] = 1
        self.assertIn("STARS EARNED", G.telemetry(c, s, G.THEMES["dark"], "t"))

    def test_metrics_match_source(self):
        s = stats_from(FakeClient())
        svg = G.telemetry(cfg(), s, G.THEMES["dark"], "t")
        self.assertIn(">3<", svg)                        # public_repos from /users
        self.assertIn(">364<", svg)                      # contributions = 52 weeks × 7 × 1
        self.assertIn("PHP 90%", svg)

    def test_activity_section_follows_threshold(self):
        c = cfg()
        low = stats_from(FakeClient(contrib_per_day=0))
        high = stats_from(FakeClient(contrib_per_day=1))
        self.assertNotIn("assets/generated/dark/activity.svg", G.build_assets(c, low))
        self.assertNotIn('href="#activity"', G.build_readme(c, low))
        self.assertIn("assets/generated/dark/activity.svg", G.build_assets(c, high))
        self.assertIn('href="#activity"', G.build_readme(c, high))

    def test_all_generated_svgs_are_valid(self):
        files = G.build_assets(cfg(), stats_from(FakeClient()))
        with tempfile.TemporaryDirectory() as d:
            for rel, content in files.items():
                p = Path(d) / Path(rel).name.replace(".svg", f"-{Path(rel).parent.name}.svg")
                p.write_text(content)
                ET.fromstring(content)
                self.assertEqual(V.check_svg(p), [], rel)

    def test_section_numbers_are_consecutive(self):
        nums = [n for _, n, _ in G.active_sections(cfg(), {"status": "pending"})]
        self.assertEqual(nums, [f"{i:02d}" for i in range(1, len(nums) + 1)])

    def test_text_is_escaped(self):
        c = cfg()
        c["identity"]["subtitle"] = "<script>alert(1)</script> & co"
        svg = G.hero(c, G.THEMES["dark"], "h")
        self.assertNotIn("<script>", svg)
        ET.fromstring(svg)


class TestRepository(unittest.TestCase):
    @unittest.skipIf(__import__("os").environ.get("PROFILE_CI"), "CI regenerates outputs after tests")
    def test_committed_outputs_are_up_to_date(self):
        self.assertEqual(G.main(["--check"]), 0, "run scripts/generate_profile_svgs.py")

    def test_validator_passes(self):
        self.assertEqual(V.main([]), 0)


if __name__ == "__main__":
    unittest.main()
