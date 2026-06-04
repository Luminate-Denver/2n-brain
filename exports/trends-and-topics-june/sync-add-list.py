#!/usr/bin/env python3
"""
Subscribe the approved add-list to AC list 2. Re-derives the set live (pull + classify),
then for buckets ADD + HOLD (CJ approved "add all of them"; test/junk skipped) does
POST /api/3/contact/sync (upsert) + POST /api/3/contactLists (status=1 subscribe).
Prints per-member results and the AC list-2 count before/after.
"""
import json, re, urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Desktop/2n-brain")
ENV_PATH = REPO / ".env"
MCP_PATH = REPO / ".mcp.json"
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


def write(method, url, headers, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={**headers, "Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def norm(e):
    return (e or "").strip().lower()


def mcp_token():
    return json.loads(MCP_PATH.read_text())["mcpServers"]["2n"]["headers"]["Authorization"].replace("Bearer ", "")


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
    docs = []
    for m in re.finditer(r"```json\s*\n(.*?)\n\s*```", text, flags=re.DOTALL):
        try:
            docs.append(json.loads(m.group(1).strip()))
        except Exception:
            pass
    p = re.search(r"Page:\s*\d+\s+of\s+(\d+)", text)
    return docs, (int(p.group(1)) if p else None)


def mcp_find_fo_users():
    out, page = [], 1
    headers = {"Authorization": f"Bearer {mcp_token()}", "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    while True:
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "findUsers",
            "arguments": {"where": json.dumps({"type": {"equals": "family-office"}}), "limit": 100, "page": page, "sort": "-createdAt"}}}
        text = http_post("https://www.2pwrn.com/api/mcp", headers, json.dumps(body))
        content = ((parse_sse(text) or {}).get("result", {}) or {}).get("content", [])
        txt = "".join(c.get("text", "") for c in content if c.get("type") == "text")
        docs, pages = extract_docs(txt)
        if not docs:
            break
        out.extend(docs)
        if pages and page >= pages:
            break
        page += 1
    return out


def ac_list(base, h):
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
    if u.get("testUser") or "test@" in email:
        return "skip"
    onb = (u.get("onboardingStatus") or "").lower()
    comp = u.get("company") or {}
    if (onb and onb != "invited") or (u.get("loginCount") or 0) > 0 or u.get("lastLoginAt") \
       or ((comp.get("profileStatus") or "").lower() not in ("", "stub")) or comp.get("active") is True:
        return "add"
    return "hold"


def main():
    base, key = env("AC_API_URL").rstrip("/"), env("AC_API_KEY")
    h = {"Api-Token": key, "Accept": "application/json"}

    ac = ac_list(base, h)
    fo = mcp_find_fo_users()
    targets = [u for u in fo if norm(u.get("email")) not in ac and classify(u) in ("add", "hold")]
    print(f"AC list 2 before: {len(ac)}")
    print(f"Adding {len(targets)} members (ADD + HOLD; test/junk skipped)\n")

    added = 0
    for u in targets:
        email = u.get("email")
        fn = (u.get("firstName") or "").strip()
        ln = (u.get("lastName") or "").strip()
        s, b = write("POST", f"{base}/api/3/contact/sync", h, {"contact": {"email": email, "firstName": fn, "lastName": ln}})
        if s >= 300:
            print(f"  ✗ {email} upsert HTTP {s}: {b[:160]}")
            continue
        cid = json.loads(b)["contact"]["id"]
        s, b = write("POST", f"{base}/api/3/contactLists", h, {"contactList": {"list": LIST_ID, "contact": int(cid), "status": 1}})
        if s >= 300:
            print(f"  ✗ {email} subscribe HTTP {s}: {b[:160]}")
            continue
        added += 1
        print(f"  ✓ {fn} {ln} <{email}> → contact {cid}, subscribed")

    after = ac_list(base, h)
    print(f"\nAdded OK: {added}/{len(targets)}")
    print(f"AC list 2 after: {len(after)}  (was {len(ac)})")


if __name__ == "__main__":
    main()
