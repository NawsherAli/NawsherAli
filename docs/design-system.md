# NAWSHER/OS Design System

All tokens live in `scripts/svgkit.py` (`THEMES`, `MONO`, `WIDTH`). Change them there, then regenerate.

## Colour
| Token | Dark | Light | Use |
|---|---|---|---|
| bg | #0A0D0B | #F7F8F4 | canvas |
| panel / panel2 | #0F1512 / #131B17 | #FFFFFF / #F1F4EE | windows, tiles, chips |
| border / grid | #22302A / #16211C | #CBD5CD / #E6ECE5 | outlines, background grid |
| text / muted / dim | #D5DED8 / #8A988F / #6A786F | #1C2420 / #55625A / #6E7A73 | type hierarchy (dim ≥ 3.8:1, used only for small notes) |
| green | #3DDC84 | #137A43 | primary accent, prompts, "online" |
| amber | #F2A541 | #9A5B00 | headlines, career facts, cursors |
| orange / cyan / red | #E9783A / #57D3E0 / #E5534B | #B24A12 / #0B7285 / #B42318 | sparing accents |

Body text and accents are ≥4.5:1 on panels in both themes (checked with the WCAG formula); "dim" is ≥3.8:1 and only used for secondary notes.

## Typography
- One family: the monospace system stack `JetBrains Mono, Fira Code, SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace`.
- Sizes: 24 (designation), 20 (section headers), 15–16 (body), 13–14 (secondary), 11–12 (labels, all caps, letter-spacing 1–1.5).
- Hero wordmark: original 5×7 pixel font (`FONT` in svgkit), 8 px cells. It's font-independent, so it looks identical everywhere.

## Layout
- Full-width assets use a 1000-unit viewBox. GitHub scales them to the column (~838 px desktop).
- Half-width cards are 490 × 390 and placed in pairs at `width="49%"`.
- Spacing scale: 4 / 8 / 12 / 16 / 20 / 24. Window chrome is a 30-unit title bar, 8-unit radius and three square LEDs.

## Components (`svgkit.py`, `generate_profile_svgs.py`)
| Component | Function | Notes |
|---|---|---|
| Document | `document()` | role="img", `<title>`, `<desc>`, grid + scanline patterns, reduced-motion CSS |
| Window | `window()` | retro terminal chrome with label |
| Section header | `section_header()` | `▌NN // LABEL ── [label.mod]` |
| Chip | `chip()` | tag with optional brand icon |
| Tile | `_tile()` | metric tile, label + value |
| Pixel text / glyphs | `pixel_text()`, `pixel_glyph()` | wordmark, cloud, mail and "in" glyphs |
| Brand icons | `icon()` | CC0 simple-icons paths, recoloured to theme |

## Motion rules
1. Animation is decoration only. The static state of every element is readable.
2. Typing uses a cover rect whose static transform is `scale(0 1)` (hidden). If CSS animations don't run, the text is simply visible.
3. `prefers-reduced-motion: reduce` disables all animation.
4. No GIFs, no external images.

## Icons
Brand marks come from simple-icons (CC0; see `assets/icons/brands/LICENSE-simple-icons-CC0.md`). AWS and LinkedIn marks aren't in simple-icons, so neutral pixel glyphs are used instead.
