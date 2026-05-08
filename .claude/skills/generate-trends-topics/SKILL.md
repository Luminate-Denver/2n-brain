---
name: generate-trends-topics
description: Compose the monthly "Trends & Topics" Family Office Brief — pulls last sent edition from ActiveCampaign for reference, ingests the month's content (Google Doc today, 2N MCP queries later), renders into the locked Direction-B template, applies orphan/widow control, exports HTML to exports/, and (on confirmation) creates a draft campaign in AC. Trigger when CJ says "build the [Month] trends & topics", "compose this month's Family Office Brief", "next T&T edition", "monthly newsletter for 2N", or anything similar.
---

# Generate Trends & Topics — Monthly Family Office Brief

Produces the AC-ready HTML for the "trends&topics (`<Month>` `<Year>`)" campaign sent to all Family Office Members. Locked design (Direction B — Private-Bank Dispatch). Content varies month to month.

## When to use

- CJ asks for the new month's edition.
- One per month, sent on or around the first business day. April 2026 sent 04/02; May 2026 in progress.
- AC campaign naming convention: `trends&topics (<Mon> YYYY)` — exactly matches prior editions (campaign IDs 33–35 are the Feb/Mar/Apr 2026 series).

## Interactive flow

Drive every decision through `AskUserQuestion`, **one question per turn**, multiple choice with the documented default suffixed `(Recommended)`. Free-text only when the answer space genuinely can't be enumerated. (See `feedback_one_question_at_a_time.md` in memory.)

### 1. Pull last sent edition (reference)

```
mcp__claude_ai_ActiveCampaign__list_campaigns
  filters.name = "Trends"
  status = "complete"
  orders.ldate = "DESC"
  limit = 5
```

Capture the most recent campaign's `id`, `name`, `ldate`, `send_amt`, `screenshot` URL, and `analytics_campaign_name` (helpful for the "(Copy)" lineage). The `get_campaign` tool returns metadata only — it does **not** return the HTML body. To get the body for visual reference:

- **Preferred:** search Gmail for the AC test send (always sent shortly before the live broadcast).
  ```
  mcp__gmail_2n__search_emails
    query: "Family Office Brief" newer_than:60d
  ```
  Read the most recent `TEST: Family Office Brief: <Month> <Year>` from `mb@2pwrn.com`. Body is the rendered email content in plain-text form — sufficient to confirm structure and section ordering month over month.
- **Fallback:** the `screenshot` URL on the campaign record (`//2pwrn.img-us3.com/_screenshot_/<uuid>.jpeg`) is publicly fetchable and shows the rendered design.

Save the parsed reference content to `exports/active-campaign/trends-and-topics-<month>.md` so subsequent runs have it.

**Note (2026-05-05):** the `claude.ai ActiveCampaign` MCP tools register fine in Claude Code — earlier sessions thought they were blocked. They aren't. Just call them.

### 2. Determine content window + volume

Standard window: **previous calendar month** (e.g. May 2026 brief recaps April activity). Volume number increments monthly — Volume V was May 2026, so Volume VI is June 2026.

`AskUserQuestion`:
- **Question:** "Confirm the edition month and content window."
- **Options:** `<Next month> — recap of last month (Recommended)`, `Custom window (specify)`.

### 3. Pull this month's content

**Today (May 2026 onwards, until automation lands):** content lives in a Google Doc CJ provides at request time.

```
mcp__claude_ai_Google_Drive__read_file_content
  fileId: <doc id from CJ>
```

If the read returns "Requested entity was not found", the doc is on a different account than `cj@przm.studio` — ask CJ to share it. May 2026 example doc id: `1cJrkor8imeC00-d7-2yVsbsgcpuOtY2prgiZEq28Mwc`.

**Future (once CJ greenlights):** derive sections automatically from 2N MCP queries — see `project_trends_topics_content_source.md` in memory. Approximate mapping:

| Section | Source query |
|---|---|
| New Family Office Members | `findUsers where={type:"family-office", createdAt: {gte: monthStart, lt: monthEnd}}` joined with their `company` |
| New Sponsor Members | `findUsers where={type:"sponsor", createdAt: ...}` joined with `sponsor` |
| Deal Spotlight | `findDeals where={createdAt: ...}` ordered by recency |
| Exponential Episode | `findPodcasts where={publishedAt: ...}` |
| Upcoming Events | `findEvents where={date: {gte: today}, lte: today + 90d}` |

Save raw content to `exports/trends-and-topics-<month>/<month>-content.md`.

### 4. Compose the HTML

Copy `templates/trends-and-topics-template.html` to `exports/trends-and-topics-<month>/trends-and-topics-<month>-v1.html`. Replace these specific zones — leave everything else alone:

**Masthead (the only frame change month-over-month):**
- `<title>` — bump month and version
- `.vol` — `Volume <Roman> ◆ <Month> <Year>`

**Letter / lede:**
- The 3 paragraphs after `<span class="drop">S</span>` — replace with this month's letter copy. Keep the drop cap on the first letter of the first paragraph (any `<span class="drop">X</span>`).
- `.stat-strip` — three stats. Each `<div class="s">` is `<div class="n">NUMBER</div><div class="l">LABEL</div>`. May used: 127 family offices / 8 new in April / 5 wks to Summit. Pick what's most newsworthy this month.
- The closing line `Here's what moved in <last month> and what to have on your radar heading into <month>.` (with `&nbsp;` between the last two words).

**Section I — Member Spotlight:**
- `<h2>` — count + verb: "Eight new family offices joined in April." Apply `&nbsp;` between the last two words.
- `.roster` table rows — one row per new FO: `<td class="nm">Name</td><td class="ct">City, ST</td>`. Keep the dotted border between rows (auto via CSS).

**Section II — Sponsor Member Program:**
- Usually boilerplate ("No new sponsors this month — by design") with a referral CTA. Update the headline if a sponsor *was* admitted, otherwise reuse.

**Section III — Deal Spotlight:**
- `.ledger` ordered list — one `<li>` per deal: `<span class="idx">01</span><span class="nm">Deal Name</span><span class="sec">Sector</span>`.
- The narrative paragraphs below are largely evergreen ("Deals are the catalyst…") — only swap if CJ supplies new copy.
- `.callout` box — italic line + bold close. May used: "Access to deals you won't find through traditional channels…" / "Engagement is what unlocks it."

**Section IV — `[2^n logo]` Intelligence:**
- Pod card content. If there's a new episode: `<div class="ep-title">` is the episode title, `<div class="ep">` is the kicker, then a paragraph of show notes.
- If no new episode (May 2026 case): use the "back catalog + guest invitation" framing.

**Section V — Inside `[2^n logo]`:**
- `<h2>Where we'll&nbsp;be.</h2>` — keep.
- `.events` grid — typically 2 events. Use `class="ev soldout"` for SOLD OUT badge, `class="ev featured"` for the dark navy featured tile (currently Denver Summit while it's the next big thing).
- `New Platform&nbsp;Features` — two `.f` cards. Left card uses the 2nTV brand mark (already inlined in template) and the h4 reads literally `2^nTV` (no space, no logo — see exception below). Right card uses the medal SVG icon in the gold circle and h4 reads `Amplifier Status` (or any other current-month feature).

### 5. Logo rules (typography)

**Never superscript "2n".** Two render modes:
- **Body text / paragraphs:** plain ASCII `2^n` (caret + n).
- **Headings, mastheads, section labels, footer:** inline 2N logo.

The template has the inline-logo SVG snippet baked in (`<svg class="logo-inline" viewBox="0 0 432 432" ...>`). To use the logo in a heading, paste that SVG inline. The full memo: `feedback_2n_logo_typography.md`.

**Exception — `2^nTV`:** the product name renders as plain ASCII text (`2^nTV`, no space) in headings, even though the rule above would push to `[logo] TV`. The dedicated 2nTV brand mark (`assets/2nTV-LogoConcept-1.svg`, inlined in the TV feature card) is the visual treatment.

**Logo size cheatsheet** (current locked values in template):
- `.brand-mark` (masthead) — 56 × 56 px.
- `.logo-inline` (default body inline, e.g. inside a `<strong>`) — 1.1em × 1.1em, vertical-align -0.22em.
- `.label-name .logo-inline` (section labels) — 1.9em × 1.9em, vertical-align -0.55em. Bigger here so it reads as a logo, not an icon.
- `.tv-mark` (2nTV feature card) — 44px tall, near-square aspect (862:833).
- `.feat .f .icon` (medal circle on Amplifier card) — 44 × 44 px circle, 23 × 23 px SVG inside.
- `.foot-mark` (footer) — 44 × 44 px, white version on navy.

### 6. Orphan / widow control

Two-layer control — both go in the template already:

1. **CSS:**
   ```css
   p, .ep-title, .pull .q { text-wrap: pretty; orphans: 3; widows: 2; }
   h1, h2, h3, h4, h5 { text-wrap: balance; }
   ```
   Modern WebKit / Chromium / Firefox honor; Outlook desktop ignores gracefully.

2. **Manual `&nbsp;`** between the last two words of:
   - every visible H2 (`Eight new family offices joined in&nbsp;April.`)
   - every section H3/H4 with multi-word ("New Platform&nbsp;Features")
   - the lede paragraphs (last two words of each)
   - sponsor close (`connecting them with&nbsp;Matt`)
   - deal narrative beats (`relationships form&nbsp;here`, `wants to&nbsp;see`, etc.)
   - episode card opening line + paragraphs
   - feature card paragraphs

This is the Outlook-desktop fallback — robust regardless of `text-wrap` support.

### 7. Local review (gate)

`open <path>` and let CJ review in the browser. Resize the window to test desktop ↔ mobile orphans hold at every viewport. Iterate on `-v2`, `-v3`, etc. as needed.

### 8. AC draft push (only after CJ sign-off) — direct REST API

The AC MCP exposes only read tools (`list_campaigns`, `get_campaign`) plus contact/list/deal mutators — **no campaign-create tool**. Use the AC REST API directly with credentials from `.env` (`AC_API_URL`, `AC_API_KEY`).

**Working endpoint mix (verified 2026-05-05 during May campaign push, campaign #36):**

1. **Create message** — v3 works:
   ```
   POST {AC_API_URL}/api/3/messages
   Header: Api-Token: {AC_API_KEY}
   Body (JSON):
     {
       "message": {
         "name": "",
         "fromname": "2^n: trends&topics",
         "fromemail": "mb@2pwrn.com",
         "reply2": "mb@2pwrn.com",
         "subject": "2^n Family Office Brief: <Month> <Year>",
         "html": "<full HTML>",
         "format": "mime",
         "charset": "utf-8",
         "encoding": "8bit",
         "language_code": "en"
       }
     }
   ```
   Returns `message.id` — capture for the next step.

2. **Create campaign** — v3 returns 405; **must use legacy v1 admin endpoint**:
   ```
   POST {AC_API_URL}/admin/api.php?api_key={AC_API_KEY}&api_action=campaign_create&api_output=json
   Header: Content-Type: application/x-www-form-urlencoded
   Body (form-encoded; brackets in keys must NOT be percent-encoded):
     type=single
     name=trends&topics (<Month> <Year>)
     status=0          # 0 = draft
     public=1
     tracklinks=all
     tracklinksanalytics=1
     trackreads=1
     trackreadsanalytics=1
     fromname=2^n: trends&topics
     fromemail=mb@2pwrn.com
     reply2=mb@2pwrn.com
     subject=2^n Family Office Brief: <Month> <Year>
     m[<msg_id>]=100   # 100% allocation to the message
     p[<list_id>]=<list_id>   # *** key AND value are both the list id; not a percentage ***
   ```
   Returns `{"id": <campaign_id>, "result_code": 1, "result_message": "Campaign saved"}`.
   **Gotcha:** `p[<id>]=<percentage>` (the obvious read of the param) returns `Invalid list id in p parameter`. The format is genuinely `p[<list_id>]=<list_id>`. `lists[<n>]=<id>` and `list[<n>]=<id>` both return "You did not provide any lists." Confirmed by trial 2026-05-05.

3. **Send a test** — v3 path 404s (`/api/3/campaign/send` doesn't exist); use legacy v1:
   ```
   GET {AC_API_URL}/admin/api.php?api_key={KEY}&api_action=campaign_send&api_output=json
       &type=mime&action=test&campaignid=<id>&messageid=<id>&email=cj@2pwrn.com
   ```
   Returns `{"result":true,"result_code":1,"result_message":"Message sent"}` on success.

**Target list:** same Family Office list April uses — list **id=2 "Active Family Office Members"** (verified via `GET /api/3/campaigns/35/campaignLists`). Reuse it.

**Inline SVG note:** the template uses inline SVG for the 2N + 2nTV logos. Gmail / Apple Mail render fine; Outlook desktop won't. For test sends to `cj@2pwrn.com` (Gmail) the inline SVG works. **Before the production send to all 177+ contacts**, swap each inline `<svg>` for an `<img>` tag pointing to a hosted PNG (upload via AC image library or use base64 data URI).

**Dark-mode / Outlook auto-inversion note:** the template explicitly opts out of dark-mode treatment with `<meta name="color-scheme" content="only light">` + `<meta name="supported-color-schemes" content="light">` + `:root { color-scheme: only light }`. We tried supporting custom dark-mode body bg (#05121f) on 2026-05-05 — Outlook (Mac + web) interpreted "light dark" as permission to auto-invert and rendered navy text on navy background, illegible. The `only light` declaration tells Outlook + Apple Mail to leave content alone. The `@media (prefers-color-scheme: dark)` rule is kept for browser preview at `file://` but email clients ignore it. **If a future revision wants real dark-mode aesthetics in email clients**, every container needs explicit `bgcolor` HTML attributes (table-based layout) plus `[data-ogsc]` / `[data-ogsb]` overrides to control Outlook specifically. Don't reintroduce `light dark` without that scaffolding in place.

**Don't send to the list.** Always leave the campaign in `status=0` (draft) for CJ + Matt to review and ship from AC.

**Reference script:** `exports/trends-and-topics-<month>/push-to-ac.py` — copy + adapt next month. Uses stdlib only, no deps.

### 8a. Pre-send: audit AC list against 2N FO directory

Before flipping the campaign from draft → scheduled, reconcile AC list 2 ("Active Family Office Members", `stringid: master-contact-list`) with the 2N MCP `findUsers where=type:family-office` set. New members added during the previous month rarely make it onto the AC list automatically.

**Script:** `exports/trends-and-topics-<month>/audit-fo-list.py` — produces `fo-list-audit.md` + `-raw.json`. Reusable monthly with no edits.

What it surfaces:
- **🔴 Missing from AC** — FO users in 2N not on list 2. Add these.
- **✏️ Name mismatches** — email matches but name differs. Mostly typographic; review and update only the meaningful ones.
- **🆕 New since previous send** — FO users created in 2N after the prior month's brief send date. Cross-checked against AC.
- **⚠️ AC orphans** — list 2 contacts not registered as FO users in 2N. Likely sponsors / founders / legacy entries; usually intentional.

To add missing members → adapt `sync-missing-members.py` (uses `POST /api/3/contact/sync` for upsert + `POST /api/3/contactLists` with `status:1` to subscribe). Always pause for explicit per-run user confirmation before executing — the harness blocks shared-system writes by default.

### 8b. 2N MCP via JSON-RPC (when MCP tools don't register)

The 2N MCP server (`https://www.2pwrn.com/api/mcp`, bearer token in `.mcp.json`) sometimes doesn't expose its tools as deferred tool schemas in a Claude Code session. When that happens, call it directly via HTTP JSON-RPC:

```
POST https://www.2pwrn.com/api/mcp
Authorization: Bearer <token from .mcp.json>
Content-Type: application/json
Accept: application/json, text/event-stream
Body: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"findUsers","arguments":{"where":"{\"type\":{\"equals\":\"family-office\"}}","limit":100,"page":1}}}
```

The response is SSE — extract the `data:` line and parse as JSON. The tool result `content[0].text` is **not** raw JSON — it's prose: `Collection: "users"\nTotal: N\nPage: P of M\n\n` followed by N fenced ` ```json {...} ``` ` blocks. Extract docs via regex `r"```json\s*\n(.*?)\n\s*```"` (DOTALL). See `audit-fo-list.py` for a working implementation.

### 9. Test send (optional)

If CJ wants a test before draft-handoff, request go-ahead first (memory: `feedback_one_question_at_a_time.md`), then send to `cj@2pwrn.com` and `cj@przm.studio`.

## Design system reference

### Brand tokens
- **Navy** `#0A1A3A` — outer 8px frame border, footer background, masthead h1, body text accents (strong, em).
- **Brand gold** `#B8870A` — 1px inner frame border, section label num + rule, kicker labels, CTA borders, feature-card icon ring.
- **Logo gold** `#a77a33` — actual fill color in the 2N + 2nTV SVG assets. *Slightly* different from brand gold; do not normalize them — keep the logo authentic.
- **Cream / paper** `#F7F1E2` (callout, pod card backgrounds), `#FAF7EE` (subtler tint), `#E0D8C5` (section dividers), `#D0C7B0` (dotted rules).
- **Navy text accents** `#2B3550` (body), `#3A4360` (deep body), `#6B6657` (mid-gray meta).

### Type
- **Inter** (400/500/600/700) — body, labels, CTAs.
- **Instrument Serif** (regular + italic) — h1/h2/h3/h4, drop cap, member name cells, ledger names, episode title, callout em.
- Fonts loaded via Google Fonts `@import` — works in all major email clients except some Outlook variants which fall back to system serif/sans cleanly.

### Frame
- 8px solid `#0A1A3A` outer border on `.wrap`.
- 12px margin then 1px solid `#B8870A` inner border on `.inner`.
- Body padding 32px on `<body>`; collapses to 0 on mobile (`@media (max-width: 600px)`).

### Section anatomy
1. **Masthead** — 56×56 brand mark, `<h1>Trends &amp; Topics</h1>`, "Family Office Brief ◆ Volume `<Roman>` ◆ `<Month> <Year>`".
2. **Letter** — drop cap (92px Instrument Serif gold), 3 paragraphs, stat strip (3 cells), kicker close.
3. **Sections I-V** — roman numeral + 13px uppercase label + 80px max-width gold rule + h2 + content.
4. **Footer** — 44px white logo, signers (Matt + Sydney centered), site/LinkedIn links, legal address.

### Specific components
- **Stat strip** — 3 cells, dotted-rule top/bottom, dotted vertical separators. Numbers in Instrument Serif 32px. Labels 10px uppercase letter-spaced gray.
- **Roster table** — 2-column. Names in Instrument Serif 16px, cities right-aligned 11px gold uppercase. Dotted rule between rows.
- **Ledger** — ordered list with `01` / `02` / `03` index column, name in Instrument Serif, sector right-aligned. Top/bottom solid 1px gold rules, dotted between items.
- **Callout box** — `#F7F1E2` background, 1px gold border, italic line + bold close.
- **Pod card** — same cream + gold border; hosts the episode block.
- **Events** — 2-col grid, 1px tan border per card. `.featured` flips to navy bg + gold accents. `.soldout` adds a filled-gold "SOLD OUT" badge.
- **Feature cards** — 2-col grid, 1px tan border. Card 1 = 2nTV mark (44px) + h4 + p. Card 2 = 44×44 gold-bordered circle with icon + h4 + p.
- **CTA** — border-bordered pill, 11px uppercase letter-spaced 0.22em, navy on transparent. `→` appended via `::after`.

## Change log (skill iteration)

- **2026-05-05** — skill created during May 2026 build. Direction B selected over editorial / modern-minimal mockups. Logo treatments + orphan control + 2nTV brand mark integration locked. AC API automation working (v3 message PUT/POST + v1 `campaign_create` + v1 `campaign_send` for tests). FO list audit + 6-member sync executed (list 2: 195 → 201 active). Mobile masthead fix: stacks volume line on `<600px` viewports. Drop cap upsized to 92pt. Sold-out events now read "At Capacity" rather than "Sold Out". Dark-mode reverted to `only light` after Outlook auto-inverted content (illegible). All scripts saved to `scripts/`.

## Files

### Skill folder (`.claude/skills/generate-trends-topics/`)
- `SKILL.md` — this file.
- `templates/trends-and-topics-template.html` — locked Direction B template, May 2026 content as the seed example. Copy + edit for each month.
- `scripts/push-to-ac.py` — first-time push: create message + create draft campaign + send first test. Edit `SUBJECT`, `CAMPAIGN_NAME`, `HTML_PATH`, `LIST_ID` constants per month.
- `scripts/update-and-test.py` — re-push: PUT updated HTML to existing message, send fresh test. Edit `CAMPAIGN_ID`, `MESSAGE_ID`, `TEST_RECIPIENTS` per month/run.
- `scripts/audit-fo-list.py` — pre-send audit: AC list 2 contacts vs 2N MCP family-office users. Reusable monthly with no edits.
- `scripts/sync-missing-members.py` — bulk-add the missing FO members the audit identifies. Edit the `MEMBERS_TO_ADD` list per run.

### Brand assets (`assets/` at repo root)
- `2^n_Logo_v2.svg` — gold inline mark (used as `<svg class="logo-inline">` in headings + masthead)
- `2^n_Logo_withCircle-White.svg` / `.png` — white-on-navy footer mark
- `2^n_Logo_withCircle_transparent-V2.png` — alt with circle (full-page brand)
- `2nTV-LogoConcept-1.svg` / `.png` — 2nTV brand mark for the TV feature card

### Per-month working files
- Reference content from past sends: `exports/active-campaign/trends-and-topics-<month>.md`
- Working files for the current month: `exports/trends-and-topics-<month>/`

## Edge cases

- **No new podcast episode this month** → use back-catalog + guest-invitation framing (see May 2026 ep-title: "No new episodes this month — but the back catalog has you&nbsp;covered.").
- **No new sponsor members** → reuse the boilerplate paragraph; flag with "by design" framing.
- **AC MCP `create_campaign` unavailable** → save final HTML to `exports/`, hand off to CJ to paste into AC manually using prior month's campaign as the "Copy from" source.
- **Drive doc not accessible** → verify the doc is shared with `cj@przm.studio`. If not, ask CJ to share or paste content into chat.
- **Long member names** — the roster `<td class="nm">` Instrument Serif 16px wraps gracefully; no special handling.
- **Featured event swap** — when Denver Summit ships (June), the `.ev.featured` slot rotates to the next anchor event. There's no auto-detection — check what CJ wants spotlighted.
