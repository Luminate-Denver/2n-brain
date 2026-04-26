---
name: generate-event-cards
description: Generate print-ready PDFs of 2N table cards (6×4") and/or name badges (3.5×2") for an event — pulls the guest list from the 2N MCP, joins with each user's member + amplifier status, renders one guest per page matching the 2N brand layout, saves locally, and uploads to Google Drive. Use when the user says "generate table cards", "generate name badges", "print assets for [event]", "cards for the [city] event", or anything similar.
---

# Generate Event Print Assets

Produces print-ready PDFs for **table cards** (6×4") and/or **name badges** (3.5×2") for an upcoming 2N event. Reference layout: `~/Library/Mobile Documents/com~apple~CloudDocs/christopherjewell/2^n/Events/Dallas/` (Table Cards + Name Badges folders, V2/V3 PDFs).

## Interactive flow

Go through these steps in order. Ask the user only for things you can't infer.

**Asking style — important:** Drive every decision through `AskUserQuestion`, **one question per turn**, with concrete multiple-choice options. Do **not** stack a numbered list of open questions in a single chat message. The first option should match the documented default, suffixed with `(Recommended)`, so the user can confirm with a single click. Free-text only when the answer space genuinely can't be enumerated (e.g. a guest's company name, an arbitrary date filter).

### 1. Identify the event

Call `mcp__2n__findEvents` (sorted `-date`, limit 10) — the schema field is `date` (not `startDate`). The result can be very large; if the tool returns a "saved to file" pointer, parse the file with a small inline Python script and extract `id`, `title`, `venue.city`, `date`, `eventType` per doc rather than re-reading the whole blob. If the user named a city, filter with `where: {"venue.city": {"contains": "<city>"}}`.

Then ask via `AskUserQuestion`:
- **Question:** "Which event are these print assets for?"
- **Options:** the next 2–3 upcoming events (soonest first, label as `<City> – <Mon DD, YYYY>`). Mark the soonest upcoming one `(Recommended)`.

Capture from the chosen event record: `id`, `title`, `venue.city`, `date`, `eventType`.

### 2. Ask what to generate

`AskUserQuestion`:
- **Question:** "What should I generate?"
- **Options:** `Both (Recommended)`, `Table cards only`, `Name badges only`.

### 3. Confirm sponsors

Read sponsors off the event record (field is typically `sponsors[]` — each has `name`, `logo` media ref, `website`).

`AskUserQuestion` (multiSelect: true):
- **Question:** "Which sponsors should appear on the cards?"
- **Options:** one option per sponsor, all preselected by default in the message ("all checked"). Pre-tick by listing every sponsor.

For each confirmed sponsor:
- Download the logo PNG from the MCP's `/api/media/file/...` URL to `exports/events/<slug>/tmp/<sponsor>.png`
- Record the `website` URL (this is what the QR code encodes)

### 4. Burskey check

`AskUserQuestion`:
- **Question:** "Are Matt or Sydney Burskey attending?"
- **Options:** `Both (Recommended)`, `Matt only`, `Sydney only`, `Neither`.

- Matt → title = `Founder`
- Sydney → title = `Associate`
- They render with no pre-name badges (no silver/gold/founding-caret) unless the user says otherwise.
- Their company field should be left empty (or ask the user).

### 5. Pull guest data

`mcp__2n__findEventGuests where={"event":{"equals":<eventId>}}` — paginate through all pages.

For each guest:
- If there's a linked `user` ref, fetch with `mcp__2n__findUsers` by ID.
- Extract `name` (prefer `fullName`, else `firstName lastName`), `company` (primary affiliation), `memberStatus`, `amplifierStatus`.
- Possible `memberStatus` values: `Founding Member`, `Member`, `null` (guest).
- Possible `amplifierStatus` values: `silver`, `gold`, `null`.
- If no linked user (rare — user confirmed everyone is registered), mark them as a plain guest (no status line).

Append the Burskeys if confirmed attending.

Sort guests alphabetically by last name.

### 6. Write the manifest

Path: `exports/events/<YYYY_MM_DD>-<CitySlug>_<EventType>/manifest.json`

Schema:
```json
{
  "event": {
    "title": "2^n Chicago Family Office Dinner",
    "city": "Chicago",
    "date": "2026_04_29",
    "eventType": "Dinner"
  },
  "sponsors": [
    {"name": "BGA", "logoPath": "tmp/bga.png", "website": "https://bga.com"},
    {"name": "Exponential", "logoPath": "tmp/exponential.png", "website": "https://exponential.com"}
  ],
  "guests": [
    {"name": "Brad Gates", "company": "Christopher Investment Company", "memberStatus": "Founding Member", "amplifierStatus": null},
    {"name": "Richard Kilby", "company": "Crain Family Office", "memberStatus": "Founding Member", "amplifierStatus": "silver"},
    {"name": "Kendall Childers", "company": "Rosewood Private Investments", "memberStatus": "Member", "amplifierStatus": null},
    {"name": "Matt Burskey", "company": "", "titleOverride": "Founder"},
    {"name": "Sydney Burskey", "company": "", "titleOverride": "Associate"}
  ]
}
```

`logoPath` is relative to the manifest file.

### 7. Render PDFs locally

First run only — install dependencies:
```bash
cd .claude/skills/generate-event-cards/scripts
python3 -m pip install -q -r requirements.txt
python3 -m playwright install chromium
```

Then render whichever were requested:
```bash
python3 .claude/skills/generate-event-cards/scripts/render.py \
  --manifest exports/events/<folder>/manifest.json \
  --type table-cards \
  --out exports/events/<folder>/2N-TableCards-V1.pdf

python3 .claude/skills/generate-event-cards/scripts/render.py \
  --manifest exports/events/<folder>/manifest.json \
  --type name-badges \
  --out exports/events/<folder>/2N-NameBadges-V1.pdf
```

### 8. Local review (gate)

Open each PDF locally with `open <path>` so the user can review before anything touches Drive. Wait for the user to confirm the design is good. If they ask for revisions, bump the version (`-V2`, `-V3`, ...) and re-render.

**Do not create Drive folders or upload anything until the user signs off on the local PDFs.**

### 9. Upload to Google Drive (only after sign-off)

Parent folder ID: `1pnVJvE13Ta-W_5IquP7eaj6iTlCya0nD`

For **each** approved PDF, create a subfolder inside the parent named:

```
YYYY_MM_DD-<City>_<EventType>-<PrintFileType>-V<N>
```

Where `PrintFileType` is `TableCards` or `NameBadges` and `<N>` matches the approved local PDF version. Example: `2026_04_29-Chicago_Dinner-NameBadges-V2`.

Use `mcp__claude_ai_Google_Drive__create_file` (or the nearest folder-create equivalent) to make the subfolder, then upload the PDF into it. Report the shareable link for each back to the user.

## Layout spec (for `render.py`)

### Shared tokens
- Brand font: **Overused Grotesk** (installed in `~/Library/Fonts/` on macOS; Chromium picks it up automatically). Fallback stack: `'Overused Grotesk', 'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif`.
- Company / family-office font: **Instrument Serif** (loaded via Google Fonts `@import` in the rendered HTML). Fallback: `'Times New Roman', Georgia, serif`.
- Brand gold: `#B8870A`
- Name navy: `#0A1A3A` (very dark navy)
- Name: navy, **weight 400 (regular)**, negative letter-spacing (`-0.07rem` table cards, `-0.038rem` name badges)
- Status: brand gold, sans (Overused Grotesk), weight 400
- Company: brand gold, **Instrument Serif**, weight 400
- **Horizontal centering**: every block on the front of the card and on the badge (brand mark, name, status line, company, sponsor row) is horizontally centered. Pre-name icons (founding caret, silver/gold check) hang left of the name via absolute positioning (`right: 100%` relative to the inline-block `.name`) so the name itself stays optically centered on the card.
- **Vertical centering**: the entire content group (`.stack` = brand mark + name-row + status + company + sponsors) is vertically centered on the page via page-level flex (`.page { display: flex; flex-direction: column; justify-content: center; align-items: center; }`). No absolute positioning of the brand mark or sponsor row — everything flows in the stack.
- Pre-name badge order, left to right: **founding-member caret → silver/gold check** (so caret comes first, check comes closer to the name)
- **Pre-icon rendering**: each icon is a `<span class="pre-icon">` with the asset set as `background-image`, locked square via min/max width+height, `flex-shrink: 0`. Table cards use `background-size: contain` (assets are 2818×2816, near-square). Name badges use `background-size: 100% 100%` because at the 0.11" badge size, Chromium's sub-pixel rounding under `contain` clips the right edge of the icon — `100% 100%` forces full fill (the assets are square enough that this introduces no visible distortion).

### Table card — front (6in × 4in, landscape)
All blocks are horizontally centered. The pre-icons sit absolutely positioned to the left of the centered name, so the name itself stays optically centered on the card.
```
          [2^n brand mark, centered, 0.55" tall]

      [pre-icons 0.245"] [ NAME, 40pt, weight 400, navy #0A1A3A, letter-spacing -0.07rem, centered ]

                [2^n mini, 0.22"] Founding Member | Member | Founder | Associate
                              (14pt, gold sans)

                  Company Name (22pt, gold, Instrument Serif)

         [sponsor logos row, centered, slot 1.4in × 0.55in per sponsor]
```

Guests with no `memberStatus` and no `titleOverride`: skip the status line entirely.

### Table card — back (6in × 4in, landscape)
Row of QR codes, one per sponsor, vertically centered on the page. Each cell:
```
[QR code, 1.3" square]
[sponsor logo, 1.2in × 0.45in slot, centered beneath]
```

### Name badge (3.5in × 2in, landscape)
Same content as the front of the table card, scaled down. All blocks horizontally centered; pre-icons absolute-positioned to the left of the centered name.
- 2^n brand mark 0.28" tall at top
- Pre-icons 0.11" square (background-size: 100% 100% — see shared tokens)
- Name 18pt, weight 400, navy #0A1A3A, letter-spacing -0.038rem
- Status line 8pt, gold sans (mini-2n 0.12" tall)
- Company 12pt, gold Instrument Serif
- Sponsors row: slot 0.65in × 0.26in per sponsor

## Assets

All paths relative to repo root (`/Users/christopherjames/Desktop/2n-brain/2n-brain/`):

- `assets/2^n_Logo_withCircle_transparent-V2.png` → brand mark (top of card)
- `assets/2^n_Logo_v2.svg` → inline mini mark (next to "Founding Member" / "Member" text)
- `assets/Silver-Check-1.png` → amplifier silver
- `assets/Gold-Check-1.png` → amplifier gold
- `assets/Founding-Member-Caret-Icon.png` → founding-member marker

## Output folder naming

Local: `exports/events/<YYYY_MM_DD>-<CitySlug>_<EventType>/` (one folder per event, both PDFs inside).

Drive: one subfolder per PDF, named `YYYY_MM_DD-<City>_<EventType>-<TableCards|NameBadges>-V1`, created inside the parent folder ID above.

## Edge cases & notes

- **Long names**: if name > 24 chars, drop font size to ~30pt on table cards / 14pt on badges.
- **Long company names**: wrap up to 2 lines, same rule.
- **Single sponsor**: center the one logo / QR.
- **Three+ sponsors**: scale logo height down so they fit side-by-side.
- **Visual balance across logos with different aspect ratios**: every sponsor logo renders inside a fixed-size `.sponsor-slot` (1.4in × 0.55in for table cards, 0.65in × 0.26in for badges). The `<img>` uses `object-fit: contain` with `max-width/max-height: 100%`, so each logo scales to fit the slot regardless of its native aspect ratio. This prevents wide wordmarks (e.g. ARCH at ~5:1) from dominating taller logos (e.g. BGA at ~2.6:1) when they sit at the same height.
- **White-on-transparent sponsor logos**: many sponsor logos are designed for dark backgrounds and are invisible on the white card. The renderer applies `filter: brightness(0)` to every `.sponsor-logo` so these logos render as solid black silhouettes. If a sponsor supplies a dark or full-color logo that should keep its native colors, override the filter for that sponsor (e.g. add a `--colored` modifier class).
- **Flag surprises**: if a user record is missing `company` or has an unexpected `memberStatus` value, list them back to the user for confirmation before rendering — don't silently render blank.
- **Version bump**: if the Drive folder `...V1` already exists, bump to `V2`, `V3`, etc.
