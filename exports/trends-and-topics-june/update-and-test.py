#!/usr/bin/env python3
"""
Update June draft (campaign #42 / message #53) with the latest v3 HTML,
then send a fresh TEST to the 3 confirmed recipients. Campaign stays draft (status 0).
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Code/2n/2n-brain")
HTML_PATH = REPO / "exports/trends-and-topics-june/trends-and-topics-june-v8.html"
ENV_PATH = REPO / ".env"
CAMPAIGN_ID = 42
MESSAGE_ID = 53
SUBJECT = "2^n Family Office Brief: June 2026 (preview v8)"  # TEMP unique subject to defeat Gmail thread-trim on repeated tests; RESTORE to "2^n Family Office Brief: June 2026" before production handoff
FROM_NAME = "2^n: trends&topics"
FROM_EMAIL = "mb@2pwrn.com"
REPLY_TO = "mb@2pwrn.com"
TEST_RECIPIENTS = ["cj@2pwrn.com"]  # v8 deal-ledger iteration — CJ-only check before broadcasting


def load_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def request(method, url, headers, body=None):
    data = None
    if body is not None:
        if isinstance(body, dict):
            data = json.dumps(body).encode("utf-8")
            headers = {**headers, "Content-Type": "application/json"}
        else:
            data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main():
    env = load_env(ENV_PATH)
    base = env["AC_API_URL"].rstrip("/")
    key = env["AC_API_KEY"]
    h = {"Api-Token": key, "Accept": "application/json"}

    html = HTML_PATH.read_text()
    print(f"Loaded HTML: {len(html)} bytes  ({HTML_PATH.name})\n")

    # ---- 1. Update message via v3 PUT ----
    print(f"[1/2] Updating message #{MESSAGE_ID} via PUT /api/3/messages/{MESSAGE_ID} …")
    payload = {
        "message": {
            "fromname": FROM_NAME,
            "fromemail": FROM_EMAIL,
            "reply2": REPLY_TO,
            "subject": SUBJECT,
            "html": html,
            "format": "mime",
            "charset": "utf-8",
            "encoding": "8bit",
            "language_code": "en",
        }
    }
    status, body = request("PUT", f"{base}/api/3/messages/{MESSAGE_ID}", h, payload)
    if status >= 300:
        print(f"  v3 PUT failed (HTTP {status}): {body[:400]}")
        return
    print(f"  → message #{MESSAGE_ID} updated.")

    # ---- 2. Send fresh test ----
    print(f"\n[2/2] Sending fresh TEST to {', '.join(TEST_RECIPIENTS)} …")
    for to in TEST_RECIPIENTS:
        params = {
            "api_key": key,
            "api_action": "campaign_send",
            "api_output": "json",
            "type": "mime",
            "action": "test",
            "campaignid": str(CAMPAIGN_ID),
            "messageid": str(MESSAGE_ID),
            "email": to,
        }
        url = f"{base}/admin/api.php?" + urllib.parse.urlencode(params)
        status, body = request("GET", url, {"Accept": "application/json"})
        snippet = body[:300].replace("\n", " ")
        print(f"  → {to}: HTTP {status} | {snippet}")

    print(f"\nDone. Campaign #{CAMPAIGN_ID} still DRAFT (status 0). Message #{MESSAGE_ID} now = v3.")


if __name__ == "__main__":
    main()
