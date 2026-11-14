# Maintenance

## Everyday changes (edit one file)
Everything personal lives in `data/profile.toml`: title, terminal lines, profile lists, timeline, career facts, stack, work cards, build queue, interests, links and thresholds.
```bash
python3 scripts/generate_profile_svgs.py   # rebuild SVGs + README
python3 scripts/validate_assets.py         # check
python3 -m unittest discover -s tests      # test
```
Pushing a change to `data/profile.toml` on `main` also triggers the workflow, which regenerates everything.

## Common tasks
| Task | Do this |
|---|---|
| A flagship repo goes public | Set its `[[lab]]` status to `BUILDING` or `SHIPPED`. It then appears in telemetry automatically (languages, recent pushes) |
| Feature a new technology | Add `[slug, label]` to a `[[stack]]` group. Add the CC0 icon from simple-icons to `assets/icons/brands/<slug>.svg`, or leave the slug empty for a text chip |
| Change colours | Edit `THEMES` in `scripts/svgkit.py` |
| Show stars/followers sooner | Lower the thresholds in `[telemetry]` |
| Add a personal website | Set `links.website`. A WEBSITE button appears in UPLINK |
| Force a refresh | Actions → update-profile → Run workflow |

## Accuracy rules
- Only add facts that are on the CV or LinkedIn.
- Employer systems stay summarised: no code, internal diagrams, security details or customer data.
- iotaiy.com is not linked: it presents an agency (IOTAIY LLC) and doesn't mention Nawsher. Link a personal site instead when one exists.

## If the workflow fails
1. Open the run log. Each step prints `[fetch]`, `[generate]` and `[validate]` lines.
2. A fetch failure is non-fatal: the old data stays and goes STALE after `stale_after_days`.
3. A validate failure blocks the commit. Fix the reported file and rerun.
