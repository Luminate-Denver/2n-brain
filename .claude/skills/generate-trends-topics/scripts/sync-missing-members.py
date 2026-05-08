#!/usr/bin/env python3
"""
Subscribe the 6 family-office members from 2N who are missing from AC list 2.
Uses POST /api/3/contact/sync (upsert) + POST /api/3/contactLists (status=1 = subscribe).
"""

import json
import urllib.request
from pathlib import Path

REPO = Path("/Users/christopherjames/Desktop/2n-brain")
ENV_PATH = REPO / ".env"
LIST_ID = 2  # "Active Family Office Members"

MEMBERS_TO_ADD = [
    {"email": "hthompson@jbpco.com",       "firstName": "Hank",          "lastName": "Thompson"},
    {"email": "gbailey@legacyknight.com",  "firstName": "Garrett",       "lastName": "Bailey"},
    {"email": "benjamin@53stations.com",   "firstName": "Ben",           "lastName": "Sack"},
    {"email": "chinedu@53stations.com",    "firstName": "Chinedu",       "lastName": "Udeogu"},
    {"email": "jamie@53stations.com",      "firstName": "Jamie",         "lastName": "Fisher"},
    {"email": "jbw@wautier.co.uk",         "firstName": "Jean-Baptiste", "lastName": "Wautier"},
]


def load_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def request(method, url, headers, body):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    if data is not None:
        headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main():
    env = load_env(ENV_PATH)
    base = env["AC_API_URL"].rstrip("/")
    h = {"Api-Token": env["AC_API_KEY"], "Accept": "application/json"}

    print(f"Syncing {len(MEMBERS_TO_ADD)} members to AC list {LIST_ID} (Active Family Office Members)\n")

    for m in MEMBERS_TO_ADD:
        # 1. Upsert contact
        upsert_payload = {
            "contact": {
                "email": m["email"],
                "firstName": m["firstName"],
                "lastName": m["lastName"],
            }
        }
        status, body = request("POST", f"{base}/api/3/contact/sync", h, upsert_payload)
        if status >= 300:
            print(f"  ✗ {m['email']} — upsert FAILED HTTP {status}: {body[:300]}")
            continue
        contact_id = json.loads(body)["contact"]["id"]
        print(f"  ✓ upsert {m['email']} → contact id {contact_id}")

        # 2. Subscribe to list 2 (status 1 = active)
        sub_payload = {
            "contactList": {
                "list": LIST_ID,
                "contact": int(contact_id),
                "status": 1,  # 1 = active subscribed
            }
        }
        status, body = request("POST", f"{base}/api/3/contactLists", h, sub_payload)
        if status >= 300:
            print(f"    ✗ subscribe FAILED HTTP {status}: {body[:300]}")
            continue
        print(f"    ✓ subscribed to list {LIST_ID}")

    print("\nDone. Refresh the May draft (#36) recipient count in AC to verify.")


if __name__ == "__main__":
    main()
