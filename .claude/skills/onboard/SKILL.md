---
name: onboard
description: Walk a new user through repo setup — reads onboarding.md for the current connection list, confirms which connections they want, then guides them through each one step-by-step. Use when the user runs /onboard or asks to set up connections, get onboarded, or configure their environment for this repo.
---

# onboard

Interactive onboarding flow for a new user of the 2n-brain repo. Pulls the canonical connection list from `onboarding.md` so the flow stays in sync as connections are added or removed.

## Flow

Work through these phases in order. Do not batch prompts — wait for each answer before moving on.

### Phase 1 — Load the current connection list

1. Read `onboarding.md` from the repo root (the `2n-brain` working directory).
2. Parse the `## Connections` section. Each bullet is one connection. Strip formatting (`*`, `**`, backticks) to get clean names.
3. Prepend `WSL` to the list **only if the user is on Windows** (ask once up front: "Are you on Windows or Mac/Linux?"). Mac/Linux users skip WSL entirely.
4. Show the user the full list you parsed so they can confirm it matches what they see in `onboarding.md`.

### Phase 2 — Opt-in per connection

Go through the list one at a time. For each connection, ask:

> Do you want to set up **{connection}**? (yes / no / skip for now)

- Record each answer in a running table in chat (connection → decision).
- Do not explain or set anything up yet. Just collect answers.
- When all have been answered, show the final table and ask: "Ready to walk through setup for the ones you said yes to?"

### Phase 3 — Guided setup

For each `yes`, walk through setup **one connection at a time**. After each one, confirm it works before moving to the next.

Use the per-connection playbooks below. If a connection appears in `onboarding.md` that is **not** in the playbooks, tell the user honestly: "I don't have a setup playbook for this one yet — let's note it and come back to it," and move on.

## Per-connection playbooks

### WSL (Windows only)

1. Open PowerShell as Administrator.
2. Run `wsl --install` and reboot when prompted.
3. After reboot, launch Ubuntu from Start menu, create a Unix username + password.
4. In Cursor: `Settings → Terminal → Default Profile → WSL`.
5. Confirm: open a new terminal in Cursor — prompt should look like `user@machine:~$`.

### Payload

1. Ask the user for their Payload admin URL (the 2n app admin panel).
2. Have them log in and copy their API token from their user settings.
3. Confirm they already have `.mcp.json` populated (the 2n MCP uses this token). If `.mcp.json` is missing, copy from `.mcp.json.example` and paste the token into the `Authorization` header.
4. Restart Claude Code so the MCP reloads.
5. Test: run `findCompanies` with an empty query — should return data.

### Gmail

1. In Claude Code, run `/mcp` and look for the Gmail server (it should appear in the available MCP list).
2. If not connected, trigger the auth flow — Claude will output a URL; open it and approve the scopes (read, send, labels, filters).
3. Test: ask Claude to "list my 5 most recent email labels."

### Granola

1. Ensure the Granola desktop app is installed and you've recorded at least one meeting.
2. In Claude Code, run `/mcp` and connect the Granola MCP (auth flow opens in browser).
3. Test: ask Claude to "list my meetings from the last 24 hours."

### Drive

1. Run `/mcp` and connect Google Drive.
2. Approve read + write scopes in the browser.
3. Test: ask Claude to "list my 5 most recently modified Drive files."

### ActiveCampaign

1. Log into ActiveCampaign → `Settings → Developer`. Copy the API URL and API Key.
2. Run `/mcp` and connect ActiveCampaign — it will prompt for URL + key (or redirect to OAuth, depending on the server version).
3. Test: ask Claude to list campaigns or contacts.

### Copper

1. Log into Copper → `Settings → Integrations → API Keys`. Generate a personal API key. Copy the key and the email it's tied to.
2. If there's a Copper MCP available in the repo config, run `/mcp` to connect. Otherwise, note this one as "pending — no MCP yet" and move on.
3. Test: query for a known company.

### LogRocket

1. Log into LogRocket → `Settings → Project → API Access`. Generate a read-only API token.
2. Store it in `.env` as `LOGROCKET_API_TOKEN=...` (do not commit).
3. If no MCP exists yet, flag it as "token stored, MCP pending" and move on.

### Knock

1. Log into Knock → `Developers → API Keys`. Copy the server key (not the public key).
2. Store in `.env` as `KNOCK_API_KEY=...`.
3. If no MCP exists yet, flag it as "token stored, MCP pending" and move on.

### Slack

1. Confirm the user is a member of the 2n Slack workspace (ask which workspace URL, e.g. `2pwrn.slack.com`).
2. In Claude Code, run `/mcp` and look for the Slack server.
3. If not connected, trigger the auth flow — open the URL Claude outputs and approve the requested scopes (channels, messages, users).
4. Confirm the workspace shown in the OAuth screen matches the 2n workspace before approving.
5. Test: ask Claude to "list the channels I'm in" or "search Slack for the last message from {name}."

### Zoom (optional — overlap with Granola)

Before setup, tell the user: **Granola already covers meeting transcripts and summaries.** Zoom MCP is only worth adding if they need live meeting metadata, recordings, chat history, or Zoom Docs/Whiteboard access that Granola doesn't give them. Ask: "Do you still want it, or skip?"

If yes:

1. Zoom has official remote MCP servers (Zoom Workspace, Zoom Docs, Zoom Whiteboard) in Zoom's MCP registry. Pick **Zoom Workspace** unless the user specifies.
2. In Claude Code, add the Zoom MCP as a custom connector — enter the Zoom Workspace MCP server URL and approve OAuth when the browser opens.
   - If Zoom requires a Client ID / Secret, direct the user to `marketplace.zoom.us` → create an OAuth app (or use an existing 2n workspace app) and copy the credentials.
   - Workspace admin may need to approve the app before it works.
3. Approve scopes for meetings, recordings, chat, and users (only what's needed).
4. Test: ask Claude to "list my Zoom meetings from the last 7 days" or "pull the recording summary for my last Zoom call."
5. If Zoom blocks the OAuth app (admin policy) or the MCP fails to connect, flag as "blocked — needs admin" and move on. Don't spend more than ~10 minutes debugging.

## Rules

- **Never skip the opt-in phase.** The user chooses what to connect; do not assume all connections are wanted.
- **One connection at a time during setup.** Do not dump all instructions at once.
- **Keep WSL conditional on OS.** Don't walk a Mac user through WSL.
- **Pull the connection list live from `onboarding.md` every run** — don't hardcode it here. If the markdown list drifts from the playbooks above, surface the discrepancy rather than silently ignoring it.
- **Never write tokens or secrets into chat, git, or any tracked file.** They go in `.env` (gitignored) or `.mcp.json` (also gitignored — verify before writing).
- **Stop and ask** if a step fails. Do not auto-retry or paper over errors.

## End of flow

Once every `yes` connection is verified, summarize:

- Connections completed ✓
- Connections skipped
- Anything flagged as "pending / no MCP yet"

Suggest next step: "Try `/weekly-deal-digest` or ask for a sponsor match report to exercise the 2n MCP."
