# Design Research

Researched 2026-11-14. Sources: trinib's profile (rendered page), the awesome-github-profiles topic and galleries, anuraghazra/github-readme-stats, lowlighter/metrics, and the GitHub Docs page "Basic writing and formatting syntax".

## What the references do well
| Reference | Strong idea | What we take | What we avoid |
|---|---|---|---|
| **trinib** | The profile feels like a place, not a document: terminal typing SVG, ASCII box art, custom dividers, games driven by issue links + Actions | Terminal storytelling, custom section dividers, Actions-generated content | Hotlinked GIFs (Imgur/Giphy/Tenor), meme cards, a dozen third-party widgets, visual noise |
| **Awesome profile galleries** | Strong hero, short identity line, grouped stack, a few honest stats | A single hero and a grouped stack | 30-badge walls, rainbow badges, trophy cabinets |
| **github-readme-stats** | Cards from the API; documents that the public instance is "best-effort" and rate-limited, and recommends a GitHub Action producing static SVGs with `GITHUB_TOKEN`; languages from bytes in non-fork repos | Same data approach, done in our own Action | Depending on a shared Vercel instance (unmaintained, rate-limited). The "rank" score (an estimate, not a GitHub metric) |
| **lowlighter/metrics** | Action-generated SVGs committed to the profile repo; templates incl. a terminal look | Action → static SVG → commit pattern | A heavy dependency for a few cards |

## GitHub rendering constraints (verified)
- `<picture>` is supported, so dark and light variants use `<source media="(prefers-color-scheme: …)">`.
- Custom anchors: `<a name="x"></a>` plus `href="#x"`.
- README images are proxied through camo and rendered as `<img>`:
  - no JavaScript and no clickable links inside an SVG, so every link is an `<a>` around the image;
  - CSS `@keyframes` inside the SVG do run, so animation is used but always ends in, or defaults to, the readable state;
  - web fonts can't load, so text uses a monospace system font stack and widths are budgeted at 0.605 em per character.
- Wide SVGs scale down on mobile. Key identity text is therefore also present as real Markdown (the summary quote, alt text, the availability line), so it stays readable and searchable.

## Original direction: NAWSHER/OS
The profile is a boot session of a fictional backend workstation:
- **Hero:** pixel-font wordmark (our own 5×7 font, no generator), a "RACK-01" panel of running services and a system status bar.
- **Sections are system modules:** `01 // SYSTEM PROFILE`, `02 // TELEMETRY`, `03 // STACK MODULES`, `04 // DEPLOYMENTS`, `05 // BUILD QUEUE`, `06 // RESEARCH QUEUE`, `07 // UPLINK`.
- **Honesty:** telemetry separates static CV facts from live GitHub API numbers. Vanity metrics stay hidden until they pass thresholds. Employer work is labelled private with no code. Planned repos are labelled PLANNED.
- **Palette:** near-black with a green tint, terminal green, muted amber. Cyan is used sparingly.

## Rejected ideas
- **Contribution snake:** the public calendar is near-empty today, so it would highlight the wrong thing. A custom heatmap turns on automatically once the threshold is met.
- **Third-party stat widgets, view counters, trophies:** unreliable, fake-feeling, or tracking.
- **Typing-SVG services:** replaced with our own SVG and a static fallback.
