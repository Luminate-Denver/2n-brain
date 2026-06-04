---
name: generate-trends-topics
description: Compose the monthly "Trends & Topics" Family Office Brief — pulls last sent edition + engagement analytics from ActiveCampaign, ingests the month's content (Google Doc today, 2N MCP queries later), renders into the locked Direction-B template, applies orphan/widow control, exports HTML to exports/, and (on confirmation) creates a draft campaign in AC. Trigger when CJ says "build the [Month] trends & topics", "compose this month's Family Office Brief", "next T&T edition", "monthly newsletter for 2N", or anything similar.
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

### 1b. Pull engagement analytics — every prior edition (and bank each new one)

Goal: understand how Family Office Members actually engage so each edition can be **tuned** (section order, subject line, CTA placement, length) instead of guessed. Run this **every** month — read the whole back-catalog *and* append the newest completed send so the longitudinal record keeps growing. This is the loop that lets the series get better over time, not just consistent.

**A. Aggregate stats per campaign.** The campaign record from Step 1's `list_campaigns` (or `get_campaign` per id) carries the counters. Pull every completed `trends&topics` edition — campaign ids 33–36 = Feb–May 2026 today; the series grows by one each month.

Key fields on the campaign object: `send_amt`, `total_amt`, `uniqueopens`, `opens`, `uniquelinkclicks`, `linkclicks`, `subscriberclicks`, `forwards` / `uniqueforwards`, `unsubscribes`, `replies`, `hardbounces`, `softbounces`.

Derived rates (compute these — AC does not return them pre-baked):

| Metric | Formula | What it tells you |
|---|---|---|
| Open rate | `uniqueopens / send_amt` | Subject line + sender + send-time pull |
| CTR | `uniquelinkclicks / send_amt` | Did the body move anyone to act |
| Click-to-open (CTOR) | `uniquelinkclicks / uniqueopens` | Content/CTA quality among readers who *did* open — the cleanest "was this edition good" signal |
| Unsub rate | `unsubscribes / send_amt` | Fatigue / relevance ceiling |
| Bounce rate | `(hardbounces + softbounces) / send_amt` | List hygiene — feeds the 8a audit |

**B. Link / section-level clicks.** *Which* sections earn the clicks is the actionable part. AC tracks per-link totals, and the template's CTAs are section-scoped (site, LinkedIn, each event, each feature card, referral, deal access), so each tracked link URL maps cleanly back to a section.

- v3: `GET /api/3/campaigns/{id}/links` → link objects; per-link click counts via the link's report data.
- Legacy v1 (usually simpler for totals): `GET {AC_API_URL}/admin/api.php?api_key={KEY}&api_action=campaign_report_link_list&campaignid={id}&api_output=json`.
- **Mark unverified until first run** — confirm the exact field/response shape the same way Step 8 verified the create/send endpoints, then date-stamp the working call here.

Roll per-link clicks up to the five sections (Member Spotlight, Sponsor, Deal Spotlight, `2^n` Intelligence, Inside `2^n`) + footer links, and rank them.

**C. Bank it — append-only ledger.** Write one row per completed campaign to `exports/active-campaign/trends-and-topics-analytics.csv`, plus a readable `…-analytics.md` digest. Columns: `campaign_id, name, send_date, sent, open_rate, ctr, ctor, unsub_rate, top_section, top_link, subject, notes`. **Never overwrite prior rows** — this is the longitudinal record. Each month adds exactly one row (the edition that just completed).

**D. Read it before composing.** Produce a 4–6 line takeaway block that Step 4 consumes:
- Best / worst editions by CTOR, with a hypothesis (subject style? lead section? event mix?).
- The 3 highest- and 3 lowest-click sections across the series.
- Subject-line patterns that correlate with higher opens (length, `Family Office Brief: <Month>` vs. variants).
- Any unsub spike tied to a specific edition or section.

**Don't over-fit.** Sample sizes are small (≈180–200 sends). One month is a weak signal — trust a pattern only once it holds across 2–3 editions, and **flag** one-off swings rather than acting on them.

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

**Apply the Step 1b analytics read first.** Let engagement history *shape*, not override, the editorial calls:
- Lead with the section that's consistently top-clicked; demote a chronically ignored section, or cut it to a one-liner.
- Mirror the subject-line shape of the highest-open editions (keep the `2^n Family Office Brief: <Month> <Year>` base unless the data clearly says otherwise).
- Put the single most-important CTA high — CTOR rewards above-the-fold asks.
- If unsubs spiked on a heavy edition, tighten length this month.

Analytics tunes **content and ordering only** — never the locked frame or design system. The zones below are still the only things you touch.

**⚠️ The template is a BULLETPROOF email build (locked 2026-06-03 after the v8 rebuild).** Table-based layout, every style **inlined**, no CSS grid/flex, no `::before`/`::after`, literal `→`/`↗` arrows, web-safe font fallbacks. That is what makes it render the same in Gmail / Outlook / Apple Mail / iOS. **When editing, change only text + URLs inside the inline-styled cells.** Never reintroduce `display:grid`/`flex`, pseudo-elements, or `<style>`-only styling, and don't rely on webfonts loading — Gmail strips all of that and the layout collapses (that exact failure — stacked stat strip, missing rules/arrows, wrong fonts — is what triggered this rebuild). Each section is bracketed by an HTML comment marker (`<!-- ===== I · MEMBER SPOTLIGHT ===== -->`); locate the marker, edit within. See **§4a — Bulletproof email rules** below before touching structure.

**Masthead** (`<!-- MASTHEAD -->`):
- `<title>` — bump month/version.
- Volume line text — `Family Office Brief <◆> Volume <Roman> <◆> <Month> <Year>` (the `◆` are `&#9670;` gold spans; the two flanking gold rules are the `border-top` side `<td>`s — leave them).

**Letter / lede** (`<!-- LETTER -->`):
- The 3 `<p>` paragraphs — replace with this month's letter. The drop cap is a `<span style="float:left;…64px…">T</span>` opening paragraph 1; keep it on the first letter. De-dash per §5a.
- Stat strip — a 3-cell `<table>`; edit the NUMBER `<div>` + LABEL `<div>` in each cell. June: 134 Family Offices / 9 New in May / 1 Wk to Summit.
- Closing line `Here's what moved in <last month>… heading into&nbsp;<month>.`

**Section I — Member Spotlight** (`<!-- I · MEMBER SPOTLIGHT -->`):
- h2 `<div>` — count + verb ("Nine new family offices joined in&nbsp;May.").
- Roster — one `<tr>` per new FO: `<td>Name</td><td align="right">City, ST</td>`. Last row drops the dotted `border-bottom`. **Verify firm names against 2N** (`findUsers`/`findCompanies`) — the June source doc had "Maklin Holdings" which 2N shows as **Malkin Holdings** (malkinholdings.com); confirm spellings before send.

**Section II — Deal Partner Program** (`<!-- II · DEAL PARTNER PROGRAM -->`; renamed from "Sponsor Member Program" 2026-06-03):
- "Sponsor Members" are now **Deal Partners** (public rename, CJ-confirmed). Use "Deal Partner" everywhere. See `project_2n_member_status_schema.md` — the Payload field may still be `User.type === "sponsor"`. Reuse boilerplate if no new partner; June welcomed Two Sigma + a Fruition Partners spotlight (video → `/dashboard/2n-tv/<id>`).

**Section III — Deal Spotlight** (`<!-- III · DEAL SPOTLIGHT -->`):
- Ledger is a `<table>`, one deal per `<tr>`: an index `<td>`, a middle `<td>` holding the **deal name (`<div>` serif) with the sector stacked *below* it (`<div>` small uppercase)** — sector-below on all viewports — and a right `<td>` with a gold **↗ deep-link** (`&#8599;&#65038;`). Each ↗ links to that specific deal: `https://www.2pwrn.com/dashboard/deals/?dealId=<id>`. Get IDs from `findDeals`; the bare `/deals/<id>` path has no view page (only `/edit`), so the **`?dealId=` query form** is the one that opens the deal. Last `<tr>` drops the dotted border.
- Narrative paragraphs + callout box are evergreen — only swap if CJ supplies new copy.

**Section IV — 2^n Intelligence** (`<!-- IV · 2^n INTELLIGENCE -->`):
- Pod card: kicker `<div>`, episode-title `<div>`, show-note `<p>`s. No new episode → back-catalog / guest-invitation framing.

**Section V — Inside 2^n** (`<!-- V · INSIDE 2^n -->`):
- Events — a single featured navy `<table>` cell (or a 2-cell `<tr>` for two events). Status badge text e.g. `★ Inaugural · Next Week` (middot, not em dash).
- New Platform Features — a 2-cell `<table>` `<tr>`. Each card = a gold-ring icon (`<td>` 44×44 with `border-radius:50%` holding a **hosted PNG**), h4, p, small CTA link. **Icons MUST be hosted PNGs** — Gmail strips inline SVG / data-URIs (that's why the CSS-bar and inline-SVG icon attempts failed). June cards: **New Directory View** (app tabbar icon = Lucide "Users", hosted PNG `content.app-us1.com/MZZPE9/2026/06/03/9a58aea4-00d1-46f0-b7d8-166c8a105cb1.png`) + **Amplifier Status** (medal PNG). Always link a new feature to its live URL (memory `feedback_link_new_features`).

### 4a. Bulletproof email rules (don't break Gmail)

The v8 rebuild exists because the old template was built like a web page and Gmail stripped half of it. Hold these invariants in every edit:
- **Layout = nested `<table role="presentation">`**, never `display:grid`/`flex`. (Grid is why the stat strip stacked in Gmail.)
- **Inline every style.** The `<style>` block carries only the webfont `@import`, mobile `@media` enhancements, and resets — never rely on it for baseline rendering.
- **No `::before`/`::after`.** Arrows are literal characters (`→` `&rarr;`, `↗` `&#8599;&#65038;`); rules are real `<td>`/`border-top` cells.
- **Fonts fall back in Gmail/Outlook.** Inline stacks are `'Instrument Serif',Georgia,'Times New Roman',serif` and `'Inter',Arial,Helvetica,sans-serif`. The real brand fonts only load in Apple Mail/iOS — pixel-identical typography in Gmail is **not achievable** (would require rendering the masthead as an image). Set this expectation; don't chase it.
- **Images must be hosted** (`content.app-us1.com`) — Gmail strips inline SVG + data-URIs and won't load custom webfonts.
- **`border-radius` circles** render round in Gmail/Apple/iOS, square in Outlook desktop — acceptable.

### 5. Logo rules (typography)

**Never superscript "2n".** Two render modes:
- **Body text / paragraphs:** plain ASCII `2^n` (caret + n).
- **Headings, mastheads, section labels, footer:** inline 2N logo.

In the bulletproof template, **every 2N logo mark is a hosted PNG `<img>`** (masthead brand mark, the IV/V section-label inline logos, the footer mark), NOT inline SVG — Gmail/Outlook strip inline SVG. To place the logo inline in a heading, reuse the hosted `<img src="https://content.app-us1.com/…">` already in the template (`logo-inline` sizing is now inline `width`/`height`/`vertical-align` on the `<img>`). The full memo: `feedback_2n_logo_typography.md`.

**Exception — `2^nTV`:** the product name renders as plain ASCII text (`2^nTV`, no space) in headings, even though the rule above would push to `[logo] TV`. The dedicated 2nTV brand mark (`assets/2nTV-LogoConcept-1.svg`, inlined in the TV feature card) is the visual treatment.

**Logo size cheatsheet** (current locked values in template):
- `.brand-mark` (masthead) — 56 × 56 px.
- `.logo-inline` (default body inline, e.g. inside a `<strong>`) — 1.1em × 1.1em, vertical-align -0.22em.
- `.label-name .logo-inline` (section labels) — 1.9em × 1.9em, vertical-align -0.55em. Bigger here so it reads as a logo, not an icon.
- `.tv-mark` (2nTV feature card) — 44px tall, near-square aspect (862:833).
- `.feat .f .icon` (medal circle on Amplifier card) — 44 × 44 px circle, 23 × 23 px SVG inside.
- `.foot-mark` (footer) — 44 × 44 px, white version on navy.

### 5a. Copy style — em dashes (CJ standard, set 2026-06-03)

**Use em dashes (—) extremely sparingly — effectively never.** CJ's standing rule, set on the June 2026 brief and applying to this and all future editions: cut em dashes by ~90%+; keep one only when a sentence genuinely can't be restructured without it. Default rewrites:
- Aside / appositive → comma pair, or parentheses.
- Dramatic pause / pivot → split into two sentences (period).
- `X — Y` label/badge separators → middot `·` (matches the brand's `·` separators, e.g. event status `★ Inaugural · Next Week`).

En dashes (–) for numeric/date ranges (`June 10–11`) are correct and exempt. After de-dashing, re-apply orphan-control `&nbsp;` on the new last-two-words of any sentence you restructured (Step 6).

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

**Images note (bulletproof template):** all logo marks + feature icons are already **hosted PNGs** (`content.app-us1.com`) — there's no inline SVG left to swap, and it renders in Gmail / Outlook / Apple Mail. Any NEW icon (e.g. a future feature card) must be uploaded to AC's image library first; reference the returned `content.app-us1.com/...` URL. **Gmail strips inline SVG and data-URIs**, so never use either for a member-facing icon.

**Gmail test-thread trim (important for test rounds):** repeated test sends with the *same subject* get threaded by Gmail, and the duplicate content collapses behind grey "•••" expanders — it looks like a broken/clipped header but isn't. For any round of repeated render tests, send each with a **unique subject** (append `(preview vN)`), so Gmail treats it as standalone. Then **restore the canonical `2^n Family Office Brief: <Month> <Year>` subject before the production handoff** — use `exports/trends-and-topics-<month>/finalize-message.py` (PUTs the message with the real subject + final HTML, no send). The real broadcast is one unique email per recipient, so it never threads/trims.

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

Default recipient is `cj@2pwrn.com`; gate adding `mb@` / `sydneyb@` with one AskUserQuestion (memory: `feedback_t_and_t_test_recipients.md`). For **repeated** render tests, use a **unique subject each round** (`(preview vN)`) to dodge Gmail thread-trim (§8), then restore the canonical subject with `finalize-message.py` before handoff. Reuse `exports/trends-and-topics-<month>/update-and-test.py` — it PUTs the latest v-N HTML to the existing message and fires the test (edit `HTML_PATH`, `SUBJECT`, `TEST_RECIPIENTS`).

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
4. **Footer** — 44px white logo, signers (Matt + Sydney centered; `.sigs` gap 80px desktop / 44px mobile), site/LinkedIn links, legal address (`2 Power N, LLC · 7730 E Belleview Ave. · Greenwood Village, CO` — updated 2026-06-03).

### Specific components
- **Stat strip** — 3 cells, dotted-rule top/bottom, dotted vertical separators. Numbers in Instrument Serif 32px. Labels 10px uppercase letter-spaced gray.
- **Roster table** — 2-column. Names in Instrument Serif 16px, cities right-aligned 11px gold uppercase. Dotted rule between rows.
- **Ledger** — ordered list with `01` / `02` / `03` index column, name in Instrument Serif, sector right-aligned. Top/bottom solid 1px gold rules, dotted between items. On `<600px` the sector wraps below the name (indented 44px to clear the index) so it never collides with a long deal name.
- **Callout box** — `#F7F1E2` background, 1px gold border, italic line + bold close.
- **Pod card** — same cream + gold border; hosts the episode block.
- **Events** — 2-col grid, 1px tan border per card. `.featured` flips to navy bg + gold accents. `.soldout` adds a filled-gold "SOLD OUT" badge.
- **Feature cards** — 2-col grid, 1px tan border. Card 1 = 2nTV mark (44px) + h4 + p. Card 2 = 44×44 gold-bordered circle with icon + h4 + p.
- **CTA** — border-bordered pill, 11px uppercase letter-spaced 0.22em, navy on transparent. `→` appended via `::after`.

## Change log (skill iteration)

- **2026-06-03 (cross-client rebuild → v8, template locked)** — **bulletproof rebuild** after Gmail rendered the old web-CSS template badly (grid stat strip stacked, `::before`/`::after` rules + CTA arrows dropped, webfonts not loaded). Template re-engineered to **table-based layout + fully inline styles, no grid/flex/pseudo-elements, literal `→`/`↗` arrows, web-safe font fallbacks** (new **§4a**). Cross-client parity confirmed Gmail ↔ Apple Mail (Gmail shows Georgia/Arial fallback — unavoidable; brand fonts only in Apple Mail/iOS). Directory icon is now the app's **real tabbar mark (Lucide "Users")** hosted as a PNG (`…/9a58aea4-…png`), superseding the earlier CSS-bar icon. Deal ledger: **sector moved below the title on all viewports**, with a gold **↗ per-deal deep-link** (`/dashboard/deals/?dealId=<id>`; IDs via `findDeals`). Footer signatures: **equal-width 150px blocks + 160px gap**. Learned: Gmail **thread-trims repeated same-subject tests** into "•••" → use unique `(preview vN)` subjects, restore canonical via `finalize-message.py`. June pre-send audit ran (201 AC vs 235 2N FO; 40 "missing" but includes test/stub/invited accounts — filter to active members before adding). Flagged likely roster typo **"Maklin" → "Malkin" Holdings**.
- **2026-06-03** — June 2026 (Vol VI) build. **Sponsor Member → Deal Partner** public rename applied (template Section II + memory). New house rule: **em dashes used sparingly** (Step 5a), applied to the template's evergreen copy. Footer **legal address → 7730 E Belleview Ave., Greenwood Village, CO**; Matt/Sydney `.sigs` gap widened 48→80px. Deal **ledger stacks sector under name on `<600px`**. Section V Directory feature uses a **CSS-drawn gold "list" icon** (no hosting, email-safe) to match the Amplifier gold-ring medal — there is no image-host token in this workspace and Gmail strips SVG/data-URIs. Analytics-driven cuts: dropped the low-click 2^nTV card + "Open the Feed" CTA. AC: message #53 + draft campaign #42; tests sent to cj@2pwrn.com + mb@ + sydneyb@.
- **2026-06-02** — added **Step 1b (engagement analytics)**: pull aggregate + link/section-level stats for every prior `trends&topics` edition, compute open / CTR / CTOR / unsub rates, maintain an append-only longitudinal ledger (`trends-and-topics-analytics.csv`), and feed a 4–6 line takeaway into Step 4 composition so each edition is tuned to maximize engagement. Step 4 now opens with an "apply the analytics read" block (content + ordering only; frame stays locked). Link-level API call (`campaign_report_link_list` / v3 `campaigns/{id}/links`) flagged **unverified pending first run**. `pull-campaign-analytics.py` to be authored on first run.
- **2026-05-05** — skill created during May 2026 build. Direction B selected over editorial / modern-minimal mockups. Logo treatments + orphan control + 2nTV brand mark integration locked. AC API automation working (v3 message PUT/POST + v1 `campaign_create` + v1 `campaign_send` for tests). FO list audit + 6-member sync executed (list 2: 195 → 201 active). Mobile masthead fix: stacks volume line on `<600px` viewports. Drop cap upsized to 92pt. Sold-out events now read "At Capacity" rather than "Sold Out". Dark-mode reverted to `only light` after Outlook auto-inverted content (illegible). All scripts saved to `scripts/`.

## Files

### Skill folder (`.claude/skills/generate-trends-topics/`)
- `SKILL.md` — this file.
- `templates/trends-and-topics-template.html` — locked **bulletproof** Direction B template (table-based, fully inlined; June 2026 content as the seed). Copy + edit per month — text/URLs only; never reintroduce grid/flex/pseudo-elements (§4a).
- `scripts/push-to-ac.py` — first-time push: create message + create draft campaign + send first test. Edit `SUBJECT`, `CAMPAIGN_NAME`, `HTML_PATH`, `LIST_ID` constants per month.
- `scripts/update-and-test.py` — re-push: PUT updated HTML to existing message, send fresh test. Edit `CAMPAIGN_ID`, `MESSAGE_ID`, `TEST_RECIPIENTS` per month/run.
- `scripts/audit-fo-list.py` — pre-send audit: AC list 2 contacts vs 2N MCP family-office users. **Per month update 3 constants** (`OUT_PATH` + `EXPORT_JSON` → current month; `APRIL_SEND_ISO` → the *prior* brief's send date), copy to `exports/trends-and-topics-<month>/`, run there. **Caveat:** pulls ALL `type:family-office` users incl. invited/stub/test accounts — filter to active members before treating "missing from AC" as an add-list.
- `scripts/sync-missing-members.py` — bulk-add the missing FO members the audit identifies. Edit the `MEMBERS_TO_ADD` list per run.
- `scripts/pull-campaign-analytics.py` — **authored 2026-06-03**; stdlib-only. Pulls aggregate + link-level stats for every completed `trends&topics` campaign, computes open/CTR/CTOR/unsub rates, rolls links up to sections, appends to the longitudinal ledger + writes the digest. Reusable monthly with no edits.

### Brand assets (`assets/` at repo root)
- `2^n_Logo_v2.svg` — gold inline mark (used as `<svg class="logo-inline">` in headings + masthead)
- `2^n_Logo_withCircle-White.svg` / `.png` — white-on-navy footer mark
- `2^n_Logo_withCircle_transparent-V2.png` — alt with circle (full-page brand)
- `2nTV-LogoConcept-1.svg` / `.png` — 2nTV brand mark for the TV feature card
- `directory-users-gold.svg` / `.png` — Lucide "Users" Directory tabbar icon (gold; matches the app), hosted for email at `content.app-us1.com/MZZPE9/2026/06/03/9a58aea4-00d1-46f0-b7d8-166c8a105cb1.png`

### Per-month working files
- Reference content from past sends: `exports/active-campaign/trends-and-topics-<month>.md`
- Engagement ledger (append-only, all editions): `exports/active-campaign/trends-and-topics-analytics.csv`
- Current-month analytics digest + takeaway block: `exports/active-campaign/trends-and-topics-analytics.md`
- Working files for the current month: `exports/trends-and-topics-<month>/` — holds `<month>-content.md`, the versioned `trends-and-topics-<month>-vN.html`, and per-run scripts: `push-to-ac.py` (first push), `update-and-test.py` (re-push + test), `finalize-message.py` (restore canonical subject + final HTML, **no send**), `audit-fo-list.py` + `fo-list-audit.md`/`-raw.json`.

## Edge cases

- **No new podcast episode this month** → use back-catalog + guest-invitation framing (see May 2026 ep-title: "No new episodes this month — but the back catalog has you&nbsp;covered.").
- **No new sponsor members** → reuse the boilerplate paragraph; flag with "by design" framing.
- **AC MCP `create_campaign` unavailable** → save final HTML to `exports/`, hand off to CJ to paste into AC manually using prior month's campaign as the "Copy from" source.
- **Drive doc not accessible** → verify the doc is shared with `cj@przm.studio`. If not, ask CJ to share or paste content into chat.
- **Long member names** — the roster `<td class="nm">` Instrument Serif 16px wraps gracefully; no special handling.
- **Featured event swap** — when Denver Summit ships (June), the `.ev.featured` slot rotates to the next anchor event. There's no auto-detection — check what CJ wants spotlighted.
