# Working in 2n Brain

This is a **data analysis workspace** for 2pwrn.com leadership. It is not the application codebase.

## What's here

- `.mcp.json` — connects to the 2n MCP, which exposes read-only lookups over the full 2n data model.
- `reports/` — finished analyses you write for the user.
- `exports/` — raw data dumps pulled from the MCP.
- `notes/` — the user's own scratch space. Don't edit unless asked.

There is **no application source** in this repo — no `src/`, no `package.json`, no backend. If the user asks to "change how the app does X," clarify: this workspace can't modify the app, but it can produce a report or proposal to hand to the engineering team.

## Available data (via the 2n MCP)

The MCP exposes `find*` tools — all read-only:

- **Entities**: `findCompanies`, `findDeals`, `findSponsors`, `findEvents`, `findEventGuests`, `findPodcasts`, `findUsers`, `findAdmins`, `findVendors`, `findSectors`, `findSegments`
- **Engagement**: `findDealVotes`, `findDealFeedback`
- **Matching**: `findMatchingCompanies`, `findMatchingCompaniesForDeal`, `findMatchingCompaniesForSponsor`, `findMatchingDeals`, `findMatchingSponsors`

Use these directly — don't guess at schemas. Call a `find*` tool with an empty/broad query first to see the shape of the data.

## Typical work

The user will mostly ask for:

- **Sponsor match reports** — who should sponsor whom, with reasoning.
- **Weekly deal digests** — new deals, voting activity, feedback themes.
- **Event guest analysis** — attendance patterns, cross-event overlap, top attendees.
- **Marketing copy from company data** — podcast blurbs, sponsor intros, deal summaries.

## Output conventions

- **Written analyses** → `reports/YYYY-MM-DD-short-slug.md` (e.g. `reports/2026-04-23-q1-sponsor-matches.md`).
- **Raw data dumps** → `exports/YYYY-MM-DD-short-slug.json` (or `.csv` when tabular).
- Use today's date (the harness injects `currentDate`).
- At the top of every report, include: the question asked, the MCP queries run, and the date.
- Prefer markdown tables over prose lists for anything comparative.

## Style

- The user is a senior operator, not a developer. Skip technical preambles; lead with findings.
- When a query returns a lot of data, summarize in the chat and save the full set to `exports/`.
- Flag data that looks stale, incomplete, or surprising — don't silently smooth over gaps.
- If a request is ambiguous ("top sponsors" — by what metric?), ask one clarifying question before pulling.

## What not to do

- Don't try to install dependencies, run build commands, or set up a dev server — there's nothing to build here, yet.
- Don't modify `.mcp.json` — the user's token lives there.
- Don't commit anything unless the user explicitly asks.
