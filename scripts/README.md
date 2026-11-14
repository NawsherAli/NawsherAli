# scripts/

Python 3.11+ (uses `tomllib`). Standard library only, no `pip install`.

| Script | Purpose |
|---|---|
| `fetch_github_stats.py` | Reads public GitHub data and writes `data/github-stats.json`. Uses `GITHUB_TOKEN` if set (needed for the contribution calendar). Exits 0 and keeps the old data on failure (`--strict` makes it exit 1) |
| `generate_profile_svgs.py` | Builds all SVGs (dark + light) and `README.md` from `data/`. `--check` exits 1 if outputs are out of date |
| `validate_assets.py` | XML validity, accessibility, forbidden SVG content, README image paths and anchors, secret scan. `--online` also requests external links (warnings only) |
| `svgkit.py` | Design system: tokens, window chrome, chips, pixel font, icons |

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/fetch_github_stats.py
python3 scripts/generate_profile_svgs.py
python3 scripts/validate_assets.py
python3 -m unittest discover -s tests -v
```
