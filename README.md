# 2n Brain

A personal workspace for querying and analyzing 2pwrn.com data through Claude Code. A place where Claude Code can pull data from the 2n API, write analyses, and save reports you want to keep.

## What you can do here

- Query the full 2n data model: companies, deals, sponsors, events, event guests, podcasts, users, admins, vendors, sectors, segments, deal votes, deal feedback.
- Ask for matching analyses: which companies match a sponsor, which deals match a company, sponsor ↔ company fit.
- Generate reports, exports, summaries, and marketing copy grounded in real data.
- Save anything Claude produces into `reports/` or `exports/` for future reference.

## Setup (one time)

1. Install [Claude Code](https://claude.com/claude-code) if you haven't already.
2. Clone this repo and `cd` into it.
3. Copy the MCP template and paste in your bearer token:
   ```bash
   cp .mcp.json.example .mcp.json
   ```
   Open `.mcp.json` and replace `REPLACE_WITH_TOKEN` with the token CJ sent you. The real `.mcp.json` is gitignored — it never gets committed.
4. Open the folder in Cursor (or any terminal) and run `claude`.

That's it. No build step, no dependencies, no backend to run.

## Daily use

Just ask Claude for what you want. A few examples:

- "Pull every sponsor active in Q1 and write a one-pager on each."
- "Find companies in the healthtech sector with 10+ deal votes — save to `reports/`."
- "Who are the top 20 event guests by number of events attended?"
- "Draft marketing copy for the next podcast based on recent deals."

Claude will save outputs into `reports/` (written analyses) or `exports/` (raw data dumps). See `CLAUDE.md` for conventions.

## Folder layout

- `reports/` — written analyses, summaries, drafts (markdown)
- `exports/` — raw data pulls (JSON / CSV)
- `notes/` — your own scratch notes
- `CLAUDE.md` — primes Claude on how to work in this repo. Edit freely.
- `.mcp.json` — your local MCP config with the bearer token. Gitignored.

## Adding Gmail / Drive / Granola later

These can be layered on top of the 2n MCP when you're ready — each needs its own auth. Ask CJ when you want to connect one.
