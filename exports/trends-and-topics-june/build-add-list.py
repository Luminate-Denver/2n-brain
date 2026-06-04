#!/usr/bin/env python3
"""
Build the proposed AC-list add-list: family-office members in 2N who are NOT on AC list 2,
filtered by real-member status (skip test/junk, HOLD invited-but-never-joined stubs,
ADD genuinely active members). READ-ONLY — adds nobody. Prints the list + projected totals.
"""
import json, re, urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Desktop/2n-brain")
ENV_PATH = REPO / ".env"
MCP_PATH = REPO / ".mcp.json"
OUT_MD = REPO / "exports/trends-and-topics-june/member-add-list.md"
LIST_ID = 2


def env(k):
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip()
    return None


def http_get(url, headers):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read().decode("utf-8")


def http_post(url, headers, body):
    with urllib.request.urlopen(urllib.request.Request(url, data=body.encode(), headers=headers, method="POST"), timeout=60) as r:
        return r.read().decode("utf-8")


def norm(e):
    return (e or "").strip().lower()


def mcp_token():
    cfg = json.loads(MCP_PATH.read_text())
    return cfg["mcpServers"]["2n"]["headers"]["Authorization"].replace("Bearer ", "")


def parse_sse(text):
    for m in re.finditer(r"^data:\s*(.+)$", text, flags=re.MULTILINE):
        try:
            obj = json.loads(m.group(1).strip())
        except Exception:
            continue
        if isinstance(obj, dict) and ("result" in obj or "error" in obj):
            return obj
    return None


def extract_docs(text):
    docs, total, pages = [], None, None
    for m in re.finditer(r"```json\s*\n(.*?)\n\s*```", text, flags=re.DOTALL):
        try:
            docs.append(json.loads(m.group(1).strip()))
        except Exception:
            pass
    m = re.search(r"Total:\s*(\d+)", text);  total = int(m.group(1)) if m else None
    m = re.search(r"Page:\s*\d+\s+of\s+(\d+)", text);  pages = int(m.group(1)) if m else None
    return docs, total, pages


def mcp_find_fo_users():
    out, page = [], 1
    headers = {"Authorization": f"Bearer {mcp_token()}", "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    while True:
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "findUsers",
            "arguments": {"where": json.dumps({"type": {"equals": "family-office"}}),
                          "limit": 100, "page": page, "sort": "-createdAt"}}}
        text = http_post("https://www.2pwrn.com/api/mcp", headers, json.dumps(body))
        parsed = parse_sse(text) or {}
        content = (parsed.get("result", {}) or {}).get("content", [])
        txt = "".join(c.get("text", "") for c in content if c.get("type") == "text")
        docs, total, pages = extract_docs(txt)
        if not docs:
            break
        out.extend(docs)
        if pages and page >= pages:
            break
        page += 1
    return out


def ac_list_emails():
    base = env("AC_API_URL").rstrip("/")
    h = {"Api-Token": env("AC_API_KEY"), "Accept": "application/json"}
    emails, offset = set(), 0
    while True:
        page = json.loads(http_get(f"{base}/api/3/contacts?listid={LIST_ID}&limit=100&offset={offset}&status=1", h))
        cs = page.get("contacts", [])
        for c in cs:
            emails.add(norm(c.get("email")))
        total = int(page.get("meta", {}).get("total", "0"))
        if offset + 100 >= total or not cs:
            break
        offset += 100
    return emails


def classify(u):
    email = norm(u.get("email"))
    if u.get("testUser") or "test@" in email or email in ("test@admin.com", "test@user.com"):
        return "skip", "test/junk account"
    onb = (u.get("onboardingStatus") or "").lower()
    logins = u.get("loginCount") or 0
    last = u.get("lastLoginAt")
    comp = u.get("company") or {}
    cstatus = (comp.get("profileStatus") or "").lower()
    cactive = comp.get("active")
    if onb and onb != "invited":
        return "add", f"onboardingStatus={onb}"
    if logins and logins > 0:
        return "add", f"logged in ({logins}x)"
    if last:
        return "add", "has logged in"
    if cstatus and cstatus != "stub":
        return "add", f"company profile={cstatus}"
    if cactive is True:
        return "add", "company active"
    return "hold", "invited, never logged in (stub profile)"


def comp_name(u):
    return ((u.get("company") or {}).get("name")) or "—"


def full_name(u):
    return f"{(u.get('firstName') or '').strip()} {(u.get('lastName') or '').strip()}".strip() or "—"


def main():
    ac = ac_list_emails()
    fo = mcp_find_fo_users()
    print(f"AC list 2 active contacts: {len(ac)}")
    print(f"2N family-office users:    {len(fo)}\n")

    missing = [u for u in fo if norm(u.get("email")) not in ac]
    add, hold, skip = [], [], []
    for u in missing:
        bucket, why = classify(u)
        (add if bucket == "add" else hold if bucket == "hold" else skip).append((u, why))

    add.sort(key=lambda x: (comp_name(x[0]).lower(), full_name(x[0]).lower()))
    hold.sort(key=lambda x: comp_name(x[0]).lower())

    def line(u, why):
        return f"  - {full_name(u)} — {comp_name(u)} — {u.get('email')}   [{why}]"

    print(f"=== ADD-LIST (recommended, real active members): {len(add)} ===")
    for u, why in add:
        print(line(u, why))
    print(f"\n=== HOLD (invited, not yet joined — your call): {len(hold)} ===")
    for u, why in hold:
        print(line(u, why))
    print(f"\n=== SKIP (test/junk): {len(skip)} ===")
    for u, why in skip:
        print(line(u, why))

    # distinct active FO firms = companies represented among (AC-listed ∪ add-list) active members
    active_now = [u for u in fo if classify(u)[0] == "add"]
    firms = {comp_name(u) for u in active_now if comp_name(u) != "—"}

    proj_list = len(ac) + len(add)
    print("\n=== TOTALS ===")
    print(f"AC list now:                 {len(ac)}")
    print(f"+ add-list:                  {len(add)}")
    print(f"= AC list after adding:      {proj_list}")
    print(f"Distinct active FO firms:    {len(firms)}")

    md = ["# Proposed member add-list — 2026-06-03", "",
          f"- AC list 2 now: **{len(ac)}** contacts",
          f"- Recommended to add: **{len(add)}**",
          f"- AC list after adding: **{proj_list}**",
          f"- Distinct active FO firms: **{len(firms)}**", "",
          f"## ADD (recommended) — {len(add)}", ""]
    for u, why in add:
        md.append(f"- **{full_name(u)}** — {comp_name(u)} — {u.get('email')}  _({why})_")
    md.append(f"\n## HOLD (invited, not yet joined) — {len(hold)}\n")
    for u, why in hold:
        md.append(f"- {full_name(u)} — {comp_name(u)} — {u.get('email')}")
    md.append(f"\n## SKIP (test/junk) — {len(skip)}\n")
    for u, why in skip:
        md.append(f"- {full_name(u)} — {u.get('email')}")
    OUT_MD.write_text("\n".join(md))
    print(f"\nSaved → {OUT_MD}")


if __name__ == "__main__":
    main()
