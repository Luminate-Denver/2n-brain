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

### 1b. Establish the guest-list source of truth

**Always ask — never assume.** The authoritative roster source varies per event and CJ defines it each run. Before anything touches the guest list, ask via `AskUserQuestion`:
- **Question:** "What's the source of truth for the guest list for this event?"
- **Options:**
  - `Event guest list in the platform (Recommended)` — pull the roster from `mcp__2n__findEventGuests` for this event (the default path; see Step 5).
  - `Local file` — CJ provides an absolute path to a local spreadsheet (xlsx / csv). Ask for the path (free-text), then parse it for the roster plus any tier columns (`Member` / `Founding Member` / `Deal Partner` / `Vendor Sponsor` / `Amp Badge`), exactly as with the emailed master list ([[feedback_event_cards_master_list]]).
  - `Google Drive link` — CJ provides a Drive file link or ID. Download it via the Drive REST API using gcloud ADC (same auth as Step 9), then parse it like the local file.

Capture the choice — **Step 5 branches on it.** Whatever the source, you may still cross-reference the *other* sources for fields the chosen one lacks (e.g. a file gives tiers but the platform carries `user.status` amplifier; the platform gives registrations but the file is the authority on who actually attends). Surface every discrepancy to CJ before rendering, per the master-list reconciliation rules.

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
- Download the logo from the MCP's `/api/media/file/...` URL to `exports/events/<slug>/tmp/<sponsor>.<ext>`, preserving whatever extension the source file uses (`.svg`, `.png`, `.jpg`).
- Record the `website` URL (this is what the QR code encodes)

**Logo format gate — non-SVG sponsors must be flagged.** After downloading, check each sponsor's file extension / Payload `mimeType`. For any sponsor whose logo is **not** an SVG (i.e. PNG / JPG / anything raster), call `AskUserQuestion` once before continuing:
- **Question:** "Sponsor logo(s) are raster (PNG/JPG): <comma-separated sponsor names>. SVG renders crisper at small print sizes and avoids the rasterization-aspect quirks we hit on NY 2026. How do you want to proceed?"
- **Options:**
  - `Pause — I'll upload SVG(s) to Payload (Recommended)` — wait for CJ to confirm the new files are in Payload, then re-fetch the sponsor record and re-download.
  - `Use the raster file(s) as-is` — proceed with the current downloads (acceptable but flagged for the record).
  - `Use a local SVG file instead` — ask CJ for the absolute path to a local `.svg` and copy it into `tmp/<sponsor>.svg`, overwriting the raster download.

Only proceed past this gate once every sponsor logo is either SVG or explicitly approved by CJ as raster.

### 4. Burskey check

`AskUserQuestion`:
- **Question:** "Are Matt or Sydney Burskey attending?"
- **Options:** `Both (Recommended)`, `Matt only`, `Sydney only`, `Neither`.

- Matt → title = `Founder`
- Sydney → title = `Associate`
- They render with no pre-name badges (no silver/gold check) unless the user says otherwise.
- Their company field should be left empty (or ask the user).

### 5. Pull guest data

**Branch on the Step 1b source of truth.** If CJ chose a **local file** or **Google Drive link**, build the roster from that file (name, company/firm, and any tier columns) and use the platform only to enrich tier/amplifier fields the file doesn't carry — then skip ahead to the status-field rules below for any platform enrichment. The `findEventGuests` pull below is the path **only when the source of truth is the platform guest list.**

`mcp__2n__findEventGuests where={"event":{"equals":<eventId>}}` — paginate through all pages. The eventGuest record already inlines a fully-expanded `user` object including `user.company`, so a separate `findUsers` call is usually unnecessary; only fall back to `findUsers` if a field you need is missing from the embedded user.

**Important — status fields are split across User and Company.** The Payload schema does not use `memberStatus` / `amplifierStatus`. The real fields that drive the status line are:

- **Founding Member** lives on Company: `user.company.foundingMember === true` → render the mini-2N logo + "Founding Member" status line. **No pre-name caret icon** (removed 2026-04-27 — the founding-caret asset is no longer used). Treat `false` / `null` / missing as no founding badge. Founding Member always wins over plain Member.
- **Member** lives on User: `user.type === "family-office"` (and not a Founding Member) → render the mini-2N logo + "Member" status line. Walk-ins (no linked user) do **not** get a Member badge — they render plain. Confirmed against the Chicago 2026 guest list on 2026-04-26.
- **Sponsor Member** lives on User: `user.type === "sponsor"` → render the mini-2N logo + "Sponsor Member" status line. The company line below the name should come from `user.sponsor.name` (e.g. Mac Hampden → "Fruition Partners, LLC"; Dan Rosenbloom → "Lafayette Street Capital"). Confirmed against the Chicago 2026 guest list on 2026-04-27.
- **Amplifier (silver / gold) lives on User: `user.status`**. Values seen in Payload: `"gold"`, `"silver"`, `null`. → render the silver/gold check as a pre-name icon (this is now the **only** pre-name icon — founding-caret is gone). Note: this is the same `status` field that's on every User record — do not confuse it with `eventGuest.status` (which is the registration approval state: `"approved"` / `"rejected"` / etc.). Confirmed against user id 152 (Benny Kay → `"gold"`) on 2026-04-26.
- Exclude any guest whose **eventGuest** `status === "rejected"`.

For each remaining guest, extract: `fullName`, `familyOfficeName` (the company string the guest used at registration — preferred for `family-office` users since it matches what they typed), `user.type` (`"family-office"` / `"sponsor"` / `null`), `user.status` (amplifier — `"silver"` / `"gold"` / `null`), `user.company.foundingMember` (boolean), `user.sponsor.name` (sponsor firm name — used as the company line for sponsor-type users), `submissionType` (`userRegistration` / `sponsor` / `guest`).

If there's no linked `user` ref (a pure walk-in), there's no member/founding/amplifier data — render as a plain guest (no status line) and flag them back to CJ before render.

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
    {"name": "Mac Hampden", "company": "Fruition Partners, LLC", "memberStatus": "Sponsor Member", "amplifierStatus": null},
    {"name": "Dan Rosenbloom", "company": "Lafayette Street Capital", "memberStatus": "Sponsor Member", "amplifierStatus": null},
    {"name": "Matt Burskey", "company": "", "titleOverride": "Founder"},
    {"name": "Sydney Burskey", "company": "", "titleOverride": "Associate"}
  ]
}
```

`logoPath` is relative to the manifest file.

**Optional per-sponsor `sizeScale`** (float, default `1.0`): multiplies the rendered logo via CSS `transform: scale()` without changing slot layout. Use when one sponsor's mark reads visually small against the others because of internal padding / mark-vs-bounding-box ratio differences (e.g. Morrison Cohen at ~1.18 alongside BGA + ARCH on NY 2026). Don't reach for this just because aspect ratios differ — only when the rendered result looks unbalanced.

### 7. Render PDFs locally

First run only — install dependencies:
```bash
cd .claude/skills/generate-event-cards/scripts
python3 -m pip install -q -r requirements.txt
python3 -m playwright install chromium
```

Then render whichever were requested. **PDF filenames must include the city** — format `2N-<City>-<Type>-V<N>.pdf` (e.g. `2N-Chicago-TableCards-V1.pdf`, `2N-Chicago-NameBadges-V1.pdf`). Use the city verbatim from the event record (no slug lowercasing — keep "Chicago", "New York", etc.; just strip spaces if multi-word, e.g. `2N-NewYork-TableCards-V1.pdf`).

```bash
python3 .claude/skills/generate-event-cards/scripts/render.py \
  --manifest exports/events/<folder>/manifest.json \
  --type table-cards \
  --out exports/events/<folder>/2N-<City>-TableCards-V1.pdf

python3 .claude/skills/generate-event-cards/scripts/render.py \
  --manifest exports/events/<folder>/manifest.json \
  --type name-badges \
  --out exports/events/<folder>/2N-<City>-NameBadges-V1.pdf
```

### 8. Local review (gate)

Open each PDF locally with `open <path>` so the user can review before anything touches Drive. Wait for the user to confirm the design is good. If they ask for revisions, bump the version (`-V2`, `-V3`, ...) and re-render.

**Do not create Drive folders or upload anything until the user signs off on the local PDFs.**

### 9. Upload to Google Drive (only after sign-off)

Parent folder ID: `1pnVJvE13Ta-W_5IquP7eaj6iTlCya0nD` — this lives on the **2N Shared Drive** (`driveId: 0AGlwTCCopkI1Uk9PVA`), so every Drive API call must include `supportsAllDrives=true`.

Create **one folder per event** inside the parent, named:

```
<City> <EventType> - MM/YYYY
```

Example: `Chicago Dinner - 04/2026`. Both approved PDFs go directly inside this single folder — no per-PDF subfolders, no version in the folder name. Versioning lives on the PDF filename (`2N-<City>-TableCards-V1.pdf`, `2N-<City>-NameBadges-V2.pdf`, etc.).

If the folder already exists for this event (re-render after revisions), reuse it — search by name inside the parent and upload the new PDF version alongside the existing files. Do not delete prior versions unless asked.

**Upload via the Drive REST API using gcloud ADC, not the MCP `create_file` tool.** The MCP tool requires the entire PDF as a base64 string parameter, and our PDFs (700KB–2MB) exceed practical tool-call sizes. The gcloud Application Default Credentials for `cj@przm.studio` already have the `https://www.googleapis.com/auth/drive` scope (set up via `gcloud auth login --enable-gdrive-access --update-adc`).

Steps:

1. Get a token: `TOKEN=$(gcloud auth application-default print-access-token)`
2. Look up or create the event folder:
   - Search: `GET https://www.googleapis.com/drive/v3/files?q=<urlencoded:name='<folder-name>' and '1pnVJvE13Ta-W_5IquP7eaj6iTlCya0nD' in parents and mimeType='application/vnd.google-apps.folder'>&supportsAllDrives=true&includeItemsFromAllDrives=true&fields=files(id,name)`. If a match is returned, reuse its `id`.
   - Otherwise create: `POST https://www.googleapis.com/drive/v3/files?supportsAllDrives=true` with body `{"name": "<folder-name>", "parents": ["1pnVJvE13Ta-W_5IquP7eaj6iTlCya0nD"], "mimeType": "application/vnd.google-apps.folder"}`. Capture the returned `id`.
3. Upload each approved PDF via multipart to `https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true&fields=id,name,webViewLink,parents` with the event folder `id` as the parent. Filename is the local PDF filename (e.g. `2N-TableCards-V1.pdf`).
4. Report the `webViewLink` from each upload response back to the user.

If the gcloud token comes back without the Drive scope, ask the user to run `gcloud auth login --enable-gdrive-access --update-adc` once, then retry.

### 10. Local cleanup (after successful upload)

Once **every** approved PDF has been uploaded and the user has the Drive links, ask via `AskUserQuestion`:
- **Question:** "Delete the local PDFs now that they're in Drive?"
- **Options:** `Delete PDFs (Recommended)`, `Keep them`.

If they confirm, delete both the rendered PDF files and their matching `.html` intermediates inside `exports/events/<folder>/` (e.g. `2N-*-TableCards-V*.pdf`, `2N-*-TableCards-V*.html`, `2N-*-NameBadges-V*.pdf`, `2N-*-NameBadges-V*.html`). The HTMLs are renderer byproducts and are usually larger than the PDFs themselves. Leave `manifest.json` and the `tmp/` folder in place — they're tiny and useful for re-rendering. Don't touch any other event folders.

## Layout spec (for `render.py`)

### Shared tokens
- Brand font: **Overused Grotesk** (installed in `~/Library/Fonts/` on macOS; Chromium picks it up automatically). Fallback stack: `'Overused Grotesk', 'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif`.
- Company / family-office font: **Instrument Serif** (loaded via Google Fonts `@import` in the rendered HTML). Fallback: `'Times New Roman', Georgia, serif`.
- Brand gold: `#a77a33` (matches the fill baked into `assets/2^n_Logo_v2.svg`; switched from the lighter `#B8870A` on 2026-05-14 after legibility issues at distance on the prior printed run — keep using the darker hex on every future render).
- Name navy: `#0A1A3A` (very dark navy)
- Name: navy, **weight 400 (regular)**, negative letter-spacing (`-0.07rem` table cards, `-0.038rem` name badges)
- Status: brand gold, sans (Overused Grotesk), weight 400
- Company / family-office name: **name navy** (`#0A1A3A`), **Instrument Serif**, weight 400 — matches the guest name color (switched from brand gold on 2026-05-15 per Matt's NY 2026 review).
- **2N logo aspect ratio is locked everywhere.** Every `<img>` rendering the 2N mark (`.brand` on the card/badge, `.mini-2n` inside the status line) must set explicit `width` and `height` to the same value plus `flex-shrink: 0` + `object-fit: contain`. Setting only `height` lets a flex container squash the width without losing height, which distorts the circle. If you add a new place that renders the 2N mark, apply the same pattern.
- **Horizontal centering**: every block on the front of the card and on the badge (brand mark, name, status line, company, sponsor row) is horizontally centered. The silver/gold amplifier check (when present) hangs left of the name via absolute positioning (`right: 100%` relative to the inline-block `.name`) so the name itself stays optically centered on the card.
- **Vertical centering**: the entire content group (`.stack` = brand mark + name-row + status + company + sponsors) is vertically centered on the page via page-level flex (`.page { display: flex; flex-direction: column; justify-content: center; align-items: center; }`). No absolute positioning of the brand mark or sponsor row — everything flows in the stack.
- **Pre-name icon**: only the silver/gold amplifier check is rendered as a pre-name icon. **Founding members no longer carry a caret pre-icon** (removed 2026-04-27) — their tier shows up only in the status line below the name. So a guest who is both Founding Member *and* gold amplifier renders with one pre-icon (the gold check) and "Founding Member" in the status line.
- **Pre-icon rendering**: the icon is a `<span class="pre-icon">` with the asset set as `background-image`, locked square via min/max width+height, `flex-shrink: 0`. Table cards use `background-size: contain` (assets are 2818×2816, near-square). Name badges use `background-size: 100% 100%` because at the 0.11" badge size, Chromium's sub-pixel rounding under `contain` clips the right edge of the icon — `100% 100%` forces full fill (the assets are square enough that this introduces no visible distortion).

### Table card — single design, printed double-sided (6in × 4in, landscape)
There is **only one design** for the table card. The printer prints it on both sides, so the back is identical to the front — the renderer emits one page per guest, no separate back PDF or back layout.

All blocks are horizontally centered. The silver/gold check (when present) sits absolutely positioned to the left of the centered name, so the name itself stays optically centered on the card.
```
          [2^n brand mark, centered, 0.55" tall]

      [silver/gold check 0.245" (if any)] [ NAME, 40pt, weight 400, navy #0A1A3A, letter-spacing -0.07rem, centered ]

                [2^n mini, 0.22"] Founding Member | Member | Sponsor Member | Founder | Associate
                              (14pt, gold sans)

                  Company Name (22pt, gold, Instrument Serif)

         [sponsor row, centered, gap 0.4in between cells]
         [each cell: logo 0.82in × 0.27in slot   →   0.18in gap   →   QR 0.34in × 0.34in directly below]
```

Each sponsor cell is a vertical stack: logo on top, then the sponsor's QR code (encoding `sponsor.website`) directly below with `0.18in` of vertical breathing room between them. The QR replaces the old back-side QR row.

Guests with no `memberStatus` and no `titleOverride`: skip the status line entirely.

### Name badge (3.5in × 2in, landscape)
Same content as the front of the table card, scaled down. All blocks horizontally centered; pre-icons absolute-positioned to the left of the centered name.
- 2^n brand mark 0.28" tall at top
- Pre-icons 0.11" square (background-size: 100% 100% — see shared tokens)
- Name 18pt, weight 400, navy #0A1A3A, letter-spacing -0.038rem
- Status line 8pt, gold sans (mini-2n 0.12" tall)
- Company 12pt, gold Instrument Serif
- Sponsors row: slot 0.52in × 0.21in per sponsor, `0.32in` horizontal gap between cells

## Assets

All paths relative to repo root (`/Users/christopherjames/Code/2n/2n-brain/2n-brain/`):

- `assets/2^n_Logo_withCircle_transparent-V2.png` → brand mark (top of card)
- `assets/2^n_Logo_v2.svg` → inline mini mark (next to "Founding Member" / "Member" / "Sponsor Member" text)
- `assets/Silver-Check-1.png` → amplifier silver (pre-name icon)
- `assets/Gold-Check-1.png` → amplifier gold (pre-name icon)
- ~~`assets/Founding-Member-Caret-Icon.png`~~ → **deprecated 2026-04-27**, no longer rendered. The founding-member tier is communicated via the status line only.

## Output folder naming

Local: `exports/events/<YYYY_MM_DD>-<CitySlug>_<EventType>/` (one folder per event, both PDFs inside).

Drive: one folder per event named `<City> <EventType> - MM/YYYY` (e.g. `Chicago Dinner - 04/2026`), created inside the parent folder ID above. Both PDFs land directly inside that one folder.

## Edge cases & notes

- **Long names**: if name > 24 chars, drop font size to ~30pt on table cards / 14pt on badges.
- **Long company names**: wrap up to 2 lines, same rule.
- **Single sponsor (locked 2026-07-31, SF 2026)**: center the one logo / QR cell and grow the logo slot **1.8× linear** (table cards `1.48in × 0.49in`, badges `0.94in × 0.38in`; QR size unchanged). Baked into `render.py` via the `sponsors--1` modifier — applied automatically when the manifest has exactly one sponsor. 1.6× left the logo's fine print illegible; 2.0× competed with the company line.
- **Two sponsors**: the 3-sponsor sizing below leaves the row looking sparse — bump the slot up (~1.2× linear) and reduce the inter-cell gap so the row reads as intentional rather than empty. Confirm with CJ before locking new dimensions.
- **Three sponsors (canonical layout — locked 2026-05-15 after the NY 2026 V4 print review)**: this is the most common case (BGA / ARCH / sponsor #3). The values below are baked into `render.py` CSS and have been signed off by CJ. **Do not change them when you have 3 sponsors — only adjust if the event has a different count.**
  - **Table cards**: slot `0.82in × 0.27in`, QR `0.34in × 0.34in`, vertical gap `0.18in` between logo and QR, horizontal gap `0.4in` between cells.
  - **Name badges**: slot `0.52in × 0.21in`, horizontal gap `0.32in` between cells.
  - **Per-sponsor balance**: when one sponsor's mark reads visually smaller than the others (because of internal padding in its source file — e.g. Morrison Cohen vs BGA / ARCH on NY 2026), tune via the `sizeScale` manifest field. **NY 2026 baseline: Morrison Cohen at `1.18`**, BGA + ARCH at default `1.0`. Reuse those exact values when the same three sponsors appear together. For a new sponsor trio, start with 1.0 across the board and only nudge a single sponsor if the print preview looks unbalanced.
- **Four+ sponsors**: hasn't shipped yet — start by shrinking the slot proportionally and reducing inter-cell gap; verify in print preview before sign-off.
- **Visual balance across logos with different aspect ratios**: every sponsor logo renders inside a fixed-size `.sponsor-slot`. The `<img>` uses `object-fit: contain` with `max-width/max-height: 100%`, so each logo scales to fit the slot regardless of its native aspect ratio. This prevents wide wordmarks (e.g. ARCH at ~5:1) from dominating taller logos (e.g. BGA at ~2.6:1) when they sit at the same height.
- **White-on-transparent sponsor logos**: many sponsor logos are designed for dark backgrounds and are invisible on the white card. The renderer applies `filter: brightness(0)` to every `.sponsor-logo` so these logos render as solid black silhouettes. **The Exponential podcast mark is the ONLY logo permitted to keep its native colors** (CJ, 2026-07-31) — its gold accents are part of the 2N brand family. This is hardcoded in `render.py` (`COLOR_KEEP_SPONSORS`, matched by sponsor name); do not add other sponsors to the whitelist without CJ's explicit say-so.
- **Flag surprises**: if a user record is missing `company` or has an unexpected `memberStatus` value, list them back to the user for confirmation before rendering — don't silently render blank.
- **Version bump**: versioning lives on the PDF filename (`-V1.pdf`, `-V2.pdf`, ...), not on the Drive folder. The event folder (`<City> <EventType> - MM/YYYY`) is reused across revisions — new versions sit alongside older ones in the same folder.
