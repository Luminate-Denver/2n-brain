#!/usr/bin/env python3
"""
Update May draft (campaign #36 / message #48) with latest v4 HTML, then send a fresh test to cj@2pwrn.com.
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Code/2n/2n-brain")
HTML_PATH = REPO / "exports/trends-and-topics-may/trends-and-topics-may-v4.html"
ENV_PATH = REPO / ".env"
CAMPAIGN_ID = 36
MESSAGE_ID = 48
SUBJECT = "2^n Family Office Brief: May 2026"
FROM_NAME = "2^n: trends&topics"
FROM_EMAIL = "mb@2pwrn.com"
REPLY_TO = "mb@2pwrn.com"
TEST_RECIPIENTS = ["cj@2pwrn.com"]  # default — ask CJ before adding mb@2pwrn.com / sydneyb@2pwrn.com / trevor@przm.studio per session


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
    print(f"Loaded HTML: {len(html)} bytes\n")

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
        # Fallback: create a new message + update campaign to reference it via v1.
        print("  Falling back: create new message + reassign on campaign …")
        msg_payload = {"message": {**payload["message"], "name": ""}}
        s2, b2 = request("POST", f"{base}/api/3/messages", h, msg_payload)
        if s2 >= 300:
            print(f"  ERROR creating new message: HTTP {s2}: {b2[:400]}")
            return
        new_msg_id = json.loads(b2)["message"]["id"]
        print(f"  → new message id: {new_msg_id}")
        # Reassign via v1 campaign_update
        v1_url = f"{base}/admin/api.php?api_key={key}&api_action=campaign_update&api_output=json"
        pairs = [
            ("id", str(CAMPAIGN_ID)),
            (f"m[{new_msg_id}]", "100"),
        ]
        body_form = "&".join(f"{urllib.parse.quote(k, safe='[]')}={urllib.parse.quote(str(v), safe='')}" for k, v in pairs)
        s3, b3 = request("POST", v1_url, {"Content-Type": "application/x-www-form-urlencoded"}, body_form)
        print(f"  campaign_update HTTP {s3}: {b3[:400]}")
        msg_for_test = new_msg_id
    else:
        print(f"  → message #{MESSAGE_ID} updated.")
        msg_for_test = MESSAGE_ID

    # ---- 2. Send fresh test ----
    print(f"\n[2/2] Sending fresh test send to {', '.join(TEST_RECIPIENTS)} …")
    for to in TEST_RECIPIENTS:
        params = {
            "api_key": key,
            "api_action": "campaign_send",
            "api_output": "json",
            "type": "mime",
            "action": "test",
            "campaignid": str(CAMPAIGN_ID),
            "messageid": str(msg_for_test),
            "email": to,
        }
        url = f"{base}/admin/api.php?" + urllib.parse.urlencode(params)
        status, body = request("GET", url, {"Accept": "application/json"})
        snippet = body[:300].replace("\n", " ")
        print(f"  → {to}: HTTP {status} | {snippet}")


if __name__ == "__main__":
    main()
