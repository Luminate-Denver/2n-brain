#!/usr/bin/env python3
"""
Restore the canonical subject on message #53 and ensure the final v8 HTML is in place.
No test send. Leaves campaign #42 as draft (status 0).
"""
import json, urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Code/2n/2n-brain")
HTML_PATH = REPO / "exports/trends-and-topics-june/trends-and-topics-june-v9.html"
ENV_PATH = REPO / ".env"
MESSAGE_ID = 53
SUBJECT = "2^n Family Office Brief: June 2026"   # canonical production subject
FROM_NAME = "2^n: trends&topics"
FROM_EMAIL = "mb@2pwrn.com"
REPLY_TO = "mb@2pwrn.com"


def env(k):
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip()
    return None


def main():
    base = env("AC_API_URL").rstrip("/")
    key = env("AC_API_KEY")
    html = HTML_PATH.read_text()
    payload = {"message": {
        "fromname": FROM_NAME, "fromemail": FROM_EMAIL, "reply2": REPLY_TO,
        "subject": SUBJECT, "html": html, "format": "mime",
        "charset": "utf-8", "encoding": "8bit", "language_code": "en",
    }}
    req = urllib.request.Request(
        f"{base}/api/3/messages/{MESSAGE_ID}",
        data=json.dumps(payload).encode(), method="PUT",
        headers={"Api-Token": key, "Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = r.status
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code}: {e.read().decode()[:400]}"); return
    print(f"Message #{MESSAGE_ID} updated → subject restored to: {SUBJECT!r}  (HTML {len(html)} bytes, from {HTML_PATH.name})")
    print("Campaign #42 remains DRAFT. No test sent.")


if __name__ == "__main__":
    main()
