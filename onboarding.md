# Onboarding

## Connections
- **Payload**
- **Gmail**
- **Granola**
- **Drive**
- **ActiveCampaign**
- **Copper**
- **LogRocket**
- **Knock**

---


## File structure starting place

- **`skills/`** — 4–5 starter skills for canonical tasks, each invokable as a slash command in Claude Code.
  - `skills/weekly-deal-digest/` → `/weekly-deal-digest`
  - `skills/sponsor-match-report/` → `/sponsor-match-report`
  - `skills/event-guest-analysis/` → `/event-guest-analysis`
  - `skills/marketing-copy-from-deals/` → `/marketing-copy-from-deals`
  - `skills/export-table/` → `/export-table` (pull a full `find*` result and save to `exports/`)
  - Each skill is a folder with a `SKILL.md` containing frontmatter (`name`, `description`, optional `allowed-tools`) plus the procedure body. Kills the blank-page cost and gives Claude a clear, reusable recipe every session.

- **`glossary.md`** — 2n-specific terminology so both Claude and the users limit conflating terms.
  - company vs. vendor vs. sponsor
  - what a "deal" actually represents
  - what "matching" means and how it's computed
  - event vs. podcast guest definitions

- **`archive/`** folder — convention: reports older than ~30 days get moved here. Keeps `reports/` clean once there are 20+ files.

- **`DECISIONS.md`** — running log of conclusions he actually acted on (e.g. "2026-04-15: set sponsor tier pricing based on X report"). Gives future Claude sessions continuity the MCP can't provide.

## Training

1. **Session hygiene**
   - `/clear` between unrelated topics
   - `/compact` when a session gets long
   - `/resume` to pick up a prior thread
   - Most new users don't know these; sessions get polluted and responses degrade.
2. **Always ask for sources**
   - "Cite the MCP query and filters you used."
   - LLMs hallucinate numbers. He should never accept a figure without the query that produced it. This is the single most important habit.
3. **Iterate, don't restart**
   - "That's close, now filter to Q1 only" beats starting over.
   - Saves context and builds on what Claude already has loaded.
4. **Save-then-summarize pattern**
   - "Pull X, save the full data to `exports/`, summarize the top 10 in chat."
   - Keeps chat context light and gives him a re-queryable artifact.
5. **Cross-check before acting**
   - Before forwarding a sponsor match or email to anyone, spot-check 2–3 data points against the live app UI.
6. **Edit `CLAUDE.md` as he learns**
   - Every time he gives the same correction twice, write it into `CLAUDE.md` so he doesn't need to say it a third time.
7. **Basic git flow**
   - `git add . && git commit -m "..." && git push`
   - If reports aren't committed, he loses them when the machine dies or the folder moves. Worth 10 minutes of live demo.

## Optional power-ups (not day one)

- **Scheduled agents / cron** — auto-generate the weekly digest every Monday morning. Overkill until he has a rhythm; compelling once he does.
- **Gmail / Drive / Granola MCPs** — wire these up the moment he says "can you email this to Matt?" or "save this to Drive" or "pull my last meeting transcript."
- **ActiveCampaign MCP** — if he wants to action marketing copy directly into campaigns instead of hand-off to the team.

## CJ's priority picks (if shipping tomorrow)

1. 3–5 starter skills in `skills/` (`/weekly-deal-digest`, `/sponsor-match-report`, plus 1–2 more)
2. `glossary.md`

Skip the rest until he tells you what he's actually doing repeatedly — premature structure is noise.
