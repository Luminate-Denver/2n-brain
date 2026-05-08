#!/usr/bin/env python3
"""
Push May edition to ActiveCampaign:
  1. POST /api/3/messages      — create the May message (HTML body)
  2. POST /api/3/campaigns     — create draft campaign on list 2 (Active Family Office Members)
  3. POST /api/3/campaign/send — send a test send to cj@2pwrn.com

Reads AC_API_URL + AC_API_KEY from .env. Writes the resulting campaign + message IDs to stdout.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Desktop/2n-brain")
HTML_PATH = REPO / "exports/trends-and-topics-may/trends-and-topics-may-v4.html"
ENV_PATH = REPO / ".env"
LIST_ID = 2  # "Active Family Office Members" — verified from campaign 35
SUBJECT = "2^n Family Office Brief: May 2026"
FROM_NAME = "2^n: trends&topics"
FROM_EMAIL = "mb@2pwrn.com"
REPLY_TO = "mb@2pwrn.com"
CAMPAIGN_NAME = "trends&topics (May 2026)"
TEST_RECIPIENTS = ["cj@2pwrn.com"]


def load_env():
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
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
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main():
    env = load_env()
    base = env["AC_API_URL"].rstrip("/")
    key = env["AC_API_KEY"]
    h = {"Api-Token": key, "Accept": "application/json"}

    html = HTML_PATH.read_text()
    print(f"Loaded HTML: {len(html)} bytes")

    # ---- 1. Create message ----
    print("\n[1/3] Creating message …")
    msg_payload = {
        "message": {
            "name": "",
            "fromname": FROM_NAME,
            "fromemail": FROM_EMAIL,
            "reply2": REPLY_TO,
            "subject": SUBJECT,
            "html": html,
            "format": "mime",
            "charset": "utf-8",
            "encoding": "8bit",
            "language_code": "en",
            "preheader_text": "",
        }
    }
    status, body = request("POST", f"{base}/api/3/messages", h, msg_payload)
    if status >= 300:
        print(f"  ERROR {status}: {body[:1500]}")
        sys.exit(1)
    msg_id = json.loads(body)["message"]["id"]
    print(f"  → message id: {msg_id}")

    # ---- 2. Create campaign (draft) — via legacy v1 API (v3 returns 405 for campaign_create) ----
    print("\n[2/3] Creating campaign (draft) via legacy v1 API …")
    v1_url = f"{base}/admin/api.php?api_key={key}&api_action=campaign_create&api_output=json"
    # AC v1 expects bracket params unencoded — build body manually rather than urlencode().
    pairs = [
        ("type", "single"),
        ("name", CAMPAIGN_NAME),
        ("sdate", ""),
        ("status", "0"),
        ("public", "1"),
        ("tracklinks", "all"),
        ("tracklinksanalytics", "1"),
        ("trackreads", "1"),
        ("trackreadsanalytics", "1"),
        ("fromname", FROM_NAME),
        ("fromemail", FROM_EMAIL),
        ("reply2", REPLY_TO),
        ("subject", SUBJECT),
        (f"m[{msg_id}]", "100"),
        # AC v1 doc format: p[<listid>]=<listid> — key AND value are both the list id.
        (f"p[{LIST_ID}]", str(LIST_ID)),
    ]
    # Keep brackets literal in keys, URL-encode values normally.
    body_form = "&".join(
        f"{urllib.parse.quote(k, safe='[]')}={urllib.parse.quote(str(v), safe='')}"
        for k, v in pairs
    )
    print(f"  body preview: {body_form[:300]}")
    h2 = {"Content-Type": "application/x-www-form-urlencoded"}
    status, body = request("POST", v1_url, h2, body_form)
    if status >= 300:
        print(f"  ERROR {status}: {body[:1500]}")
        sys.exit(1)
    parsed = json.loads(body) if body.strip().startswith("{") else {"_raw": body[:500]}
    cmp_id = parsed.get("id") or parsed.get("campaignid") or parsed.get("0")
    print(f"  → response: {json.dumps(parsed, indent=2)[:1500]}")
    if not cmp_id:
        print("  Could not parse campaign id from response.")
        sys.exit(1)
    print(f"  → campaign id: {cmp_id}")

    # ---- 3. Send test ----
    print("\n[3/3] Sending test send via legacy v1 campaign_send …")
    for to in TEST_RECIPIENTS:
        params = {
            "api_key": key,
            "api_action": "campaign_send",
            "api_output": "json",
            "type": "mime",
            "action": "test",
            "campaignid": str(cmp_id),
            "messageid": str(msg_id),
            "email": to,
        }
        url = f"{base}/admin/api.php?" + urllib.parse.urlencode(params)
        status, body = request("GET", url, {"Accept": "application/json"})
        snippet = body[:500].replace("\n", " ")
        print(f"  → test → {to}: HTTP {status} | {snippet}")

    print("\nDone.")
    print(f"  Campaign #{cmp_id} (draft) — review at: https://2pwrn.activehosted.com/campaign/{cmp_id}/designer")
    print(f"  Message #{msg_id}")


if __name__ == "__main__":
    main()
