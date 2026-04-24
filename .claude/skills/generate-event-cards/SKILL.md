---
name: generate-event-cards
description: Generate print-ready PDFs of 2N table cards (6×4") and/or name badges (3.5×2") for an event — pulls the guest list from the 2N MCP, joins with each user's member + amplifier status, renders one guest per page matching the 2N brand layout, saves locally, and uploads to Google Drive. Use when the user says "generate table cards", "generate name badges", "print assets for [event]", "cards for the [city] event", or anything similar.
---

# Generate Event Print Assets

Produces print-ready PDFs for **table cards** (6×4") and/or **name badges** (3.5×2") for an upcoming 2N event. Reference layout: `~/Library/Mobile Documents/com~apple~CloudDocs/christopherjewell/2^n/Events/Dallas/` (Table Cards + Name Badges folders, V2/V3 PDFs).

## Interactive flow

Go through these steps in order. Ask the user only for things you can't infer.

### 1. Identify the event

Call `mcp__2n__findEvents` (sorted `-startDate`, limit 10). If the user named a city, filter with `where: {city: {contains: "<city>"}}`. Confirm with the user: title + city + date.

Capture from the event record: `id`, `title`, `city`, `startDate`, `eventType`.

### 2. Ask what to generate

"Table cards, name badges, or both?" — default both.

### 3. Confirm sponsors

Read sponsors off the event record (field is typically `sponsors[]` — each has `name`, `logo` media ref, `website`). Show the list and ask: **"Include all of these? Anyone to exclude?"**

For each confirmed sponsor:
- Download the logo PNG from the MCP's `/api/media/file/...` URL to `exports/events/<slug>/tmp/<sponsor>.png`
- Record the `website` URL (this is what the QR code encodes)

### 4. Burskey check

Ask: **"Are Matt Burskey and/or Sydney Burskey attending? [matt / syd / both / neither]"**

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

### 7. Render PDFs

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

After rendering, open each PDF locally (`open <path>`) so the user can review before upload.

### 8. Upload to Google Drive

Parent folder ID: `1pnVJvE13Ta-W_5IquP7eaj6iTlCya0nD`

For **each** generated PDF, create a subfolder inside the parent named:

```
YYYY_MM_DD-<City>_<EventType>-<PrintFileType>-V1
```

Where `PrintFileType` is `TableCards` or `NameBadges`. Example: `2026_04_29-Chicago_Dinner-NameBadges-V1`.

Use `mcp__claude_ai_Google_Drive__create_file` (or the nearest folder-create equivalent) to make the subfolder, then upload the PDF into it. Report the shareable link for each back to the user.

## Layout spec (for `render.py`)

### Shared tokens
- Brand font: **Overused Grotesk** (installed in `~/Library/Fonts/` on macOS; Chromium picks it up automatically). Fallback stack: `'Overused Grotesk', 'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif`.
- Brand gold: `#B8870A`
- Name: black, tight-ish letter-spacing, Light weight (300)
- Status + company: brand gold
- Pre-name badge order, left to right: **founding-member caret → silver/gold check** (so caret comes first, check comes closer to the name)

### Table card — front (6in × 4in, landscape)
```
          [2^n brand mark, centered, 0.55" tall, 0.45" from top]

      [pre-icons 0.3"] [ NAME, ~38pt, centered ]

                [2^n mini] Founding Member | Member | Founder | Associate
                              (14pt, gold)

                       Company Name (18pt, gold)

         [sponsor logos row, centered, 0.5" tall, 0.45" from bottom]
```

Guests with no `memberStatus` and no `titleOverride`: skip the status line entirely.

### Table card — back (6in × 4in, landscape)
Row of QR codes, one per sponsor, vertically centered on the page. Each cell:
```
[QR code, 1.3" square]
[sponsor logo, 0.4" tall, centered beneath]
```

### Name badge (3.5in × 2in, landscape)
Same content as the front of the table card, scaled down:
- 2^n brand mark 0.28" tall at top
- Pre-icons 0.18"
- Name ~17pt
- Status line ~8pt
- Company ~10pt
- Sponsors row ~0.22" tall at bottom

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
- **Flag surprises**: if a user record is missing `company` or has an unexpected `memberStatus` value, list them back to the user for confirmation before rendering — don't silently render blank.
- **Version bump**: if the Drive folder `...V1` already exists, bump to `V2`, `V3`, etc.
