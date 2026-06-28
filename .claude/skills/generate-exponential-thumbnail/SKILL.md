---
name: generate-exponential-thumbnail
description: Generate a new Exponential podcast episode thumbnail (8000×4500 JPG) that is visually identical to the shipped E1–E9 thumbnails — same background, "PRESENTED BY 2^n", "Exponential" wordmark, and hosts line; only the gold bottom band's episode title and guest subtitle change. Use when the user says "new Exponential thumbnail", "generate the Episode #N thumbnail", "make the podcast thumbnail for [guest/company]", or similar.
---

# Generate Exponential Thumbnail

Produces the next Exponential podcast episode thumbnail, pixel-identical to the
existing series except for the two lines of text in the gold bottom band.

The whole thumbnail above the band — the city-lights background texture,
`PRESENTED BY 2^n`, the `Exponential` wordmark (with the gold-triangle "A"), and
the hosts line (`with Kyle Shoemaker & Matt Burskey`) — is a **constant**. It
lives baked into `assets/base-plate.png` and is reused verbatim every episode.
This skill only types the new **title** and **subtitle** into the empty gold
band, so the result is guaranteed to match the series.

> Co-host note: the hosts line was `… & Brett Kaplan` for E1–E9; from E10 on it
> is `… & Matt Burskey`. The base plate now carries Matt Burskey. If it changes
> again, see **Changing the hosts line** below — don't hand-edit the plate.

The original source is `_Exponential-All_Thumbnails.indd` (InDesign). This skill
reproduces the band typography (Overused Grotesk) so no InDesign round-trip is
needed.

## Inputs to collect

From the user, get:
- **Episode number** → formatted zero-padded to 3 digits (`10` → `#010`).
- **Episode title** → the part after the number. Keep the established pattern,
  e.g. `Fireside Chat — Wautier Family Office`. Use an **em dash `—`** (with
  spaces) as the separator, matching E9 (`Fireside Chat — W5 Group`), even if the
  user typed a hyphen.
- **Guest(s)** → rendered as the subtitle `with <Guest>` (e.g.
  `with Jean-Baptiste (JB) Wautier`, or `with Celine Winter & Ryan Munoz` for two).

So the two band lines are:
- **Title:**  `Episode #010: Fireside Chat — Wautier Family Office`
- **Subtitle:** `with Jean-Baptiste (JB) Wautier`

If anything is ambiguous (number, exact title wording, whether to use "&" vs
"and"), ask one quick clarifying question before rendering.

## Render

The band text is rendered with **system Google Chrome** (driven by Playwright)
so that pair kerning + CSS `letter-spacing` match InDesign's spacing model — a
plain Pillow draw spaces letters character-by-character with no kerning, which
reads as too tight on multi-pair words. Dependencies (already present on this
machine):
- `python3 -c "import PIL, playwright"` — Pillow + Playwright.
- System Chrome at `/Applications/Google Chrome.app` (used via
  `channel="chrome"`; the downloadable Playwright Chromium is **not** required).
- `~/Library/Fonts/OverusedGrotesk-Roman.otf` (embedded into the page as a
  base64 data-URL; the script hard-fails if the font doesn't load, so it can
  never silently fall back to a serif).

Render:
```bash
python3 .claude/skills/generate-exponential-thumbnail/scripts/render_thumbnail.py \
  --title "Episode #010: Fireside Chat — Wautier Family Office" \
  --subtitle "with Jean-Baptiste (JB) Wautier" \
  --out /tmp/Exponential-Thumbnail-E10.jpg
```

The script renders each line as a transparent layer in Chrome, then composites
it onto the base plate with Pillow (so the background stays pixel-perfect). It
prints the auto-fit font size per line. Normal-length titles render at the
family-standard size 440; long titles auto-shrink (em-tracking preserved) to
stay off the band edges (E10's title fits at ~387).

## Review gate

Open the output for the user to review **before** saving to the canonical
folder:
```bash
open /tmp/Exponential-Thumbnail-E10.jpg
```
If they want changes, re-render. Only after sign-off, save to the series folder
(same naming convention as the others):

```
~/Library/Mobile Documents/com~apple~CloudDocs/christopherjewell/2^n/Exponential Podcast/Thumbnails/Exponential-Thumbnail-E<N>.jpg
```

Do not overwrite an existing episode file without confirming.

## Calibration (how the constants were derived)

All values in `scripts/render_thumbnail.py` were reverse-engineered by measuring
the shipped E1–E9 JPGs (8000×4500). They are **locked** — don't change them
unless the source design changes.

- **Canvas:** 8000×4500 (16:9). All episodes.
- **Gold band:** solid `#A67A33` (166,122,51), hard-edged rectangle from
  y=3088 to y=4072 (985px), full width. Uniform across all episodes.
- **Below-band strip:** thin light texture (`#E6E6E8`) from y=4073 to bottom —
  part of the base plate.
- **Font:** Overused Grotesk **Roman** for both band lines (confirmed lower MAE
  vs Medium against E9; the INDD references only Overused Grotesk + Minion Pro,
  and the band is sans). `~/Library/Fonts/OverusedGrotesk-Roman.otf`.
- **Title:** black `#000`, centered (cx=4000), size 440 (cap height ~290px),
  `letter-spacing` **−0.045em** (CJ preference — the E9-matched value was −0.0798em
  but read too tight; loosened to −0.045em on E10). Vertical: ink-top =
  baseline − 0.6545·size. Full-size baseline = y=3577 (E9).
- **Subtitle:** white `#FFF`, centered (cx=4000), size 280, `letter-spacing`
  −0.0528em. Vertical: ink-top = baseline − 0.7036·size (ascender-driven — "with…"
  always carries ascenders). Full-size baseline = y=3903 (E9).
- **Vertical centering rule:** the title + subtitle are placed as **one group**
  centered on a fixed axis (`GROUP_CENTER` = 3596, the E9 block center of
  title-cap-top↔subtitle-baseline), with the subtitle a fixed `LEADING` = 326px
  below the title baseline. So `title_baseline = GROUP_CENTER − (LEADING −
  0.6545·title_size)/2`. At full size this reduces to E9's 3577/3903 exactly; when
  a long title **shrinks**, the whole block rides up to stay centered so the top
  and bottom gaps grow together (instead of the title dropping and ballooning the
  gap above it). Verified: E10 block center 3614 ≈ E9 3621.
- **Auto-fit / safe-margin rule:** a title must keep a side margin like the rest
  of the series, so its rendered ink width is capped at **6600px** (≈82% of width,
  ~9% margin per side) — the average of the shipped titles (E5 6880 / E6 6592 /
  E7 6489 / E8 6543 / E9 6413 → ~6580). Normal-length titles fall under this and
  render at full size 440; an over-long title (e.g. E10) **shrinks** until it fits,
  em letter-spacing preserved so the tightness stays constant (E10 lands at size
  ~332, 81.9% width, 9% margins — matching E9's ~10%). The fit is **iterative**
  and measures in a wide (3000-logical) viewport so a full-size long title isn't
  clipped during measurement (that clipping was a bug that left E10 at 90% width).
  Floor 280px.
- **Hosts line** (in the base plate, not the band): gold `#A67A33`, Overused
  Grotesk Roman, size 344, `letter-spacing` −0.0686em, baseline y=2556,
  **right-aligned** to ink-right x=6991 (the wordmark's right edge), with a soft
  drop shadow (`text-shadow: 5px 8px 10px rgba(0,0,0,0.22)` in device px). Erased
  for re-lettering by copying a clean background strip (the bg there is flat
  ~`#E9E9EB`, std ~4, sparse stars) — the gold-only mask alone leaves the shadow
  as a ghost, so the whole text+shadow band (y 2316–2632) is replaced.

The starting letter-spacing values were found by binary-searching CSS
`letter-spacing` until the Chrome-rendered **ink width** matched the measured E9
ink widths (title 6413px → −0.0798em, subtitle 3411px → −0.0528em); re-rendering
E9's own text reproduced the band at MAE ≈ 12.6, the best of every method tried.
The title was then loosened to −0.045em per CJ's preference (it read tight at the
E9-exact value); the subtitle stays at the E9-matched −0.0528em.

**Known residual:** an exact pixel overlay of the reproduced title against real
E9 shows the interior drifting ~1% from the ends (which align perfectly). This is
present identically whether kerning is on or off, so it's InDesign's *Optical*
kerning (Adobe's own algorithm) distributing space differently than the font's
metric kern table — not replicable without reimplementing that algorithm. It is
imperceptible in isolation (only visible when two versions are superimposed) and
does not affect a standalone thumbnail.

**Why Chrome and not Pillow:** the first cut drew the band character-by-character
in Pillow, which disables pair kerning. Total tracking matched E9 but words with
several kern pairs (e.g. "Wautier Family Office") read as too tight. Rendering in
Chrome with `font-kerning:normal` + CSS `letter-spacing` fixed it.

## Assets

- `assets/base-plate.png` — 8000×4500, E9 with the band wiped to clean gold. The
  constant top half of every thumbnail.
- `scripts/render_thumbnail.py` — the render engine (parametric; locked constants).
- `scripts/make_base_plate.py` — regenerate the base plate from a newer episode
  JPG if the above-band design ever changes:
  ```bash
  python3 scripts/make_base_plate.py --src ".../Exponential-Thumbnail-E9.jpg"
  ```
- `scripts/update_hosts.py` — rewrite the hosts line in the base plate (see
  **Changing the hosts line**).
- `assets/base-plate-brett-kaplan.png` — the E1–E9 base plate (hosts = Brett
  Kaplan), kept for reference/revert. `assets/base-plate-prev.png` is the
  auto-backup written by `update_hosts.py`.

## Changing the hosts line

The hosts line is part of the base plate. To swap a co-host, don't hand-edit the
plate — run:
```bash
python3 .claude/skills/generate-exponential-thumbnail/scripts/update_hosts.py \
  --hosts "with Kyle Shoemaker & Matt Burskey"
```
It erases the current line (copying a clean background strip over the
text+shadow), redraws the new line with the locked gold/font/shadow/right-align,
backs up the old plate to `assets/base-plate-prev.png`, and overwrites
`assets/base-plate.png`. Re-render any affected episodes afterward.

## Notes & edge cases

- **Episode number** is always 3-digit zero-padded (`#009`, `#010`, `#011`).
- **Separator** in the title is an em dash `—` with surrounding spaces.
- **One guest vs two:** subtitle is `with A` or `with A & B`.
- **Very long titles:** they auto-shrink so they keep a safe side margin like the
  rest of the series (the 6600px cap / safe-margin rule above) — they will render
  noticeably smaller than a short title, and that's intended. If one shrinks so
  far it looks too small, shorten the wording with the user rather than raising
  the cap or the floor.
- **Output is large** (8000×4500, ~3–4MB JPG) to match the existing series; saved
  with `quality=95, subsampling=0` to preserve the crisp band text.
