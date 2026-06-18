#!/usr/bin/env python3
"""
Audit AC list 2 (Active Family Office Members) against 2N MCP family-office users.

Output: a markdown report listing
  - FO users in 2N but missing from AC list 2 (need to be added)
  - AC contacts whose name differs from 2N (potential update)
  - AC contacts on the list whose email isn't a known FO user in 2N (orphan / sponsor / non-FO?)
  - Members added to 2N since 2026-04-02 (the April brief send date)

Reads AC creds from .env, 2N MCP token from .mcp.json.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path("/Users/christopherjames/Code/2n/2n-brain")
ENV_PATH = REPO / ".env"
MCP_PATH = REPO / ".mcp.json"
OUT_PATH = REPO / "exports/trends-and-topics-may/fo-list-audit.md"
EXPORT_JSON = REPO / "exports/trends-and-topics-may/fo-list-audit-raw.json"
LIST_ID = 2
APRIL_SEND_ISO = "2026-04-02T00:00:00Z"  # April brief sent 2026-04-02


def load_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def http_get(url, headers):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def http_post(url, headers, body):
    data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def parse_sse(text):
    """Parse SSE event stream — extract every `data:` line (regex), try each as JSON.
    Return the first dict that has a JSON-RPC `result` or `error`."""
    for m in re.finditer(r"^data:\s*(.+)$", text, flags=re.MULTILINE):
        payload = m.group(1).strip()
        try:
            obj = json.loads(payload)
        except Exception:
            continue
        if isinstance(obj, dict) and ("result" in obj or "error" in obj):
            return obj
    return None


def extract_payload_docs_from_text(text_content):
    """The 2N MCP findX tools return text like:
        Collection: "users"
        Total: N documents
        Page: 1 of M

        ```json
        {... doc 1 ...}
        ```
        ```json
        {... doc 2 ...}
        ```
    Extract all JSON code blocks → list of dicts. Also parse Total + Page count from the header.
    """
    docs = []
    # Match every fenced ```json ... ``` block (multiline, non-greedy).
    for m in re.finditer(r"```json\s*\n(.*?)\n\s*```", text_content, flags=re.DOTALL):
        block = m.group(1).strip()
        try:
            docs.append(json.loads(block))
        except Exception as e:
            print(f"  WARN: could not parse block: {e}; preview: {block[:120]}")

    total = None
    pages = None
    m = re.search(r"Total:\s*(\d+)\s+documents", text_content)
    if m:
        total = int(m.group(1))
    m = re.search(r"Page:\s*(\d+)\s+of\s+(\d+)", text_content)
    if m:
        pages = int(m.group(2))
    return docs, total, pages


# ---------- AC ----------

def ac_pull_all_contacts(env):
    base = env["AC_API_URL"].rstrip("/")
    h = {"Api-Token": env["AC_API_KEY"], "Accept": "application/json"}
    out = []
    offset = 0
    page_size = 100
    while True:
        url = f"{base}/api/3/contacts?listid={LIST_ID}&limit={page_size}&offset={offset}&status=1"
        body = http_get(url, h)
        page = json.loads(body)
        contacts = page.get("contacts", [])
        out.extend(contacts)
        total = int(page.get("meta", {}).get("total", "0"))
        if offset + page_size >= total or not contacts:
            break
        offset += page_size
    return out


# ---------- 2N MCP ----------

def mcp_token():
    cfg = json.loads(MCP_PATH.read_text())
    return cfg["mcpServers"]["2n"]["headers"]["Authorization"].replace("Bearer ", "")


def mcp_call(method, params=None):
    url = "https://www.2pwrn.com/api/mcp"
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    headers = {
        "Authorization": f"Bearer {mcp_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    text = http_post(url, headers, json.dumps(body))
    parsed = parse_sse(text)
    if parsed is None:
        try:
            parsed = json.loads(text)
        except Exception:
            raise RuntimeError(f"Could not parse MCP response: {text[:300]}")
    if "error" in parsed:
        raise RuntimeError(f"MCP error: {parsed['error']}")
    return parsed.get("result", parsed)


def mcp_tool_call(name, arguments):
    params = {"name": name, "arguments": arguments}
    return mcp_call("tools/call", params)


def mcp_pull_all_family_office_users():
    """Paginate through findUsers where type=family-office.
    Tool returns text content with fenced ```json``` blocks per doc."""
    out = []
    page = 1
    while True:
        result = mcp_tool_call("findUsers", {
            "where": json.dumps({"type": {"equals": "family-office"}}),
            "limit": 100,
            "page": page,
            "sort": "-createdAt",
        })
        content = result.get("content", [])
        text_content = ""
        for c in content:
            if c.get("type") == "text":
                text_content += c.get("text", "")
        docs, total, total_pages = extract_payload_docs_from_text(text_content)
        if not docs:
            break
        out.extend(docs)
        print(f"  page {page}/{total_pages or '?'} — {len(docs)} docs (total so far: {len(out)} / {total})")
        if total_pages and page >= total_pages:
            break
        page += 1
        if page > 200:  # safety
            print("  WARN: hit page safety cap of 200")
            break
    return out


# ---------- Diff ----------

def normalize_email(e):
    return (e or "").strip().lower()


def main():
    env = load_env(ENV_PATH)

    print("Pulling AC list 2 contacts …")
    ac_contacts = ac_pull_all_contacts(env)
    print(f"  → {len(ac_contacts)} active AC contacts on list 2")

    print("Pulling 2N family-office users via MCP …")
    fo_users = mcp_pull_all_family_office_users()
    print(f"  → {len(fo_users)} family-office users in 2N")

    # Index AC by email
    ac_by_email = {}
    for c in ac_contacts:
        e = normalize_email(c.get("email"))
        if e:
            ac_by_email[e] = c

    # Index 2N FO users by email
    fo_by_email = {}
    for u in fo_users:
        e = normalize_email(u.get("email"))
        if e:
            fo_by_email[e] = u

    # 1. FO users missing from AC list
    missing_in_ac = []
    for e, u in fo_by_email.items():
        if e not in ac_by_email:
            missing_in_ac.append(u)

    # 2. Name mismatches (potential updates)
    name_diffs = []
    for e, u in fo_by_email.items():
        if e in ac_by_email:
            ac = ac_by_email[e]
            ac_name = f"{(ac.get('firstName') or '').strip()} {(ac.get('lastName') or '').strip()}".strip()
            fo_name = f"{(u.get('firstName') or '').strip()} {(u.get('lastName') or '').strip()}".strip()
            if ac_name and fo_name and ac_name.lower() != fo_name.lower():
                name_diffs.append({"email": e, "ac": ac_name, "fo": fo_name})

    # 3. AC contacts not matching any 2N FO user (orphans / non-FO)
    orphans = []
    for e, c in ac_by_email.items():
        if e not in fo_by_email:
            orphans.append(c)

    # 4. FO users created since April 2 (the April brief send)
    new_since_april = []
    for u in fo_users:
        created = u.get("createdAt") or u.get("cdate") or ""
        if created and created >= APRIL_SEND_ISO:
            new_since_april.append(u)

    # ---- Save raw + report ----
    raw = {
        "ac_contacts_count": len(ac_contacts),
        "fo_users_count": len(fo_users),
        "missing_in_ac": [
            {"email": u.get("email"), "firstName": u.get("firstName"), "lastName": u.get("lastName"),
             "createdAt": u.get("createdAt"), "id": u.get("id")} for u in missing_in_ac
        ],
        "name_diffs": name_diffs,
        "orphans_in_ac": [
            {"email": c.get("email"), "firstName": c.get("firstName"), "lastName": c.get("lastName"),
             "id": c.get("id"), "cdate": c.get("cdate")} for c in orphans
        ],
        "new_fo_since_april_2": [
            {"email": u.get("email"), "firstName": u.get("firstName"), "lastName": u.get("lastName"),
             "createdAt": u.get("createdAt"), "id": u.get("id")} for u in new_since_april
        ],
    }
    EXPORT_JSON.write_text(json.dumps(raw, indent=2, default=str))

    # Markdown report
    today = datetime.utcnow().date().isoformat()
    md = []
    md.append(f"# Active Family Office Members list audit — {today}")
    md.append("")
    md.append(f"- AC list 2 active contacts: **{len(ac_contacts)}**")
    md.append(f"- 2N family-office users: **{len(fo_users)}**")
    md.append("")
    md.append(f"## 🔴 Missing from AC list ({len(missing_in_ac)})")
    md.append("")
    md.append("Family-office users in 2N who are NOT on AC list 2. Likely the most important section — these members won't receive the May brief unless added.")
    md.append("")
    if missing_in_ac:
        md.append("| Email | Name | 2N created | 2N user id |")
        md.append("|---|---|---|---|")
        for u in sorted(missing_in_ac, key=lambda x: x.get("createdAt") or ""):
            email = u.get("email") or ""
            name = f"{(u.get('firstName') or '').strip()} {(u.get('lastName') or '').strip()}".strip() or "—"
            cdate = (u.get("createdAt") or "")[:10]
            md.append(f"| {email} | {name} | {cdate} | {u.get('id')} |")
    else:
        md.append("_None — every 2N FO user is on the AC list._")
    md.append("")
    md.append(f"## ✏️ Name mismatches ({len(name_diffs)})")
    md.append("")
    md.append("Email matches but the name in AC differs from 2N. Worth a manual look.")
    md.append("")
    if name_diffs:
        md.append("| Email | AC name | 2N name |")
        md.append("|---|---|---|")
        for d in name_diffs:
            md.append(f"| {d['email']} | {d['ac']} | {d['fo']} |")
    else:
        md.append("_None._")
    md.append("")
    md.append(f"## 🆕 New FO users since April brief (created ≥ {APRIL_SEND_ISO[:10]}) ({len(new_since_april)})")
    md.append("")
    md.append("All family-office users created in 2N since the April brief was sent. Cross-reference with the 'Missing from AC' list above to confirm sync status.")
    md.append("")
    if new_since_april:
        md.append("| Email | Name | Created | On AC list? |")
        md.append("|---|---|---|---|")
        for u in sorted(new_since_april, key=lambda x: x.get("createdAt") or ""):
            email = u.get("email") or ""
            name = f"{(u.get('firstName') or '').strip()} {(u.get('lastName') or '').strip()}".strip() or "—"
            cdate = (u.get("createdAt") or "")[:10]
            on_ac = "✅" if normalize_email(email) in ac_by_email else "❌"
            md.append(f"| {email} | {name} | {cdate} | {on_ac} |")
    else:
        md.append("_None._")
    md.append("")
    md.append(f"## ⚠️  AC contacts not in 2N FO directory ({len(orphans)})")
    md.append("")
    md.append("Active AC contacts on list 2 whose email isn't a registered family-office user in 2N. May be: sponsors, walk-ins, legacy contacts, the founders' own emails, or stale records. Worth scanning.")
    md.append("")
    if orphans:
        md.append("| Email | Name | AC id | Added to AC |")
        md.append("|---|---|---|---|")
        for c in sorted(orphans, key=lambda x: x.get("cdate") or ""):
            email = c.get("email") or ""
            name = f"{(c.get('firstName') or '').strip()} {(c.get('lastName') or '').strip()}".strip() or "—"
            cdate = (c.get("cdate") or "")[:10]
            md.append(f"| {email} | {name} | {c.get('id')} | {cdate} |")
    else:
        md.append("_None._")
    md.append("")

    OUT_PATH.write_text("\n".join(md))
    print(f"\nReport: {OUT_PATH}")
    print(f"Raw:    {EXPORT_JSON}")
    print(f"\nSummary:")
    print(f"  Missing from AC: {len(missing_in_ac)}")
    print(f"  Name mismatches: {len(name_diffs)}")
    print(f"  New FO since 04/02: {len(new_since_april)}")
    print(f"  AC orphans (not FO in 2N): {len(orphans)}")


if __name__ == "__main__":
    main()
