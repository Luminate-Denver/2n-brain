#!/usr/bin/env python3
"""
pull-campaign-analytics.py — Trends & Topics engagement analytics (Step 1b).

Pulls every completed `trends&topics` campaign from ActiveCampaign, computes
open / CTR / CTOR / unsub rates, rolls per-link clicks up to newsletter sections,
and maintains the append-only longitudinal ledger + a human-readable digest.

Stdlib only. Reads AC_API_URL / AC_API_KEY from .env (searched upward from CWD).
Reusable monthly with no edits — it skips campaigns already in the ledger and
appends only newly-completed editions.

Endpoints (verified 2026-06-03):
  - GET /api/3/campaigns?filters[name]=Trends&orders[sdate]=DESC   -> aggregate counters
  - GET /api/3/campaigns/{id}/links                                -> per-link uniquelinkclicks/linkclicks
  - GET /api/3/messages/{messageid}                                -> subject line

Outputs (under <repo>/exports/active-campaign/):
  - trends-and-topics-analytics.csv   (append-only ledger; one row per completed edition)
  - trends-and-topics-analytics.md    (full digest + cross-series takeaway)
"""
import csv
import json
import os
import urllib.parse
import urllib.request

# ---------- locate repo + creds ----------
def find_repo():
    d = os.getcwd()
    while True:
        if os.path.exists(os.path.join(d, ".env")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("Could not find .env walking up from CWD")
        d = parent

REPO = find_repo()

def envval(key):
    with open(os.path.join(REPO, ".env")) as f:
        for line in f:
            s = line.strip()
            if s.startswith(key + "="):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    return None

BASE = envval("AC_API_URL").rstrip("/")
KEY = envval("AC_API_KEY")
HDR = {"Api-Token": KEY, "Accept": "application/json"}

OUT_DIR = os.path.join(REPO, "exports", "active-campaign")
CSV_PATH = os.path.join(OUT_DIR, "trends-and-topics-analytics.csv")
MD_PATH = os.path.join(OUT_DIR, "trends-and-topics-analytics.md")

# ---------- http ----------
def get_json(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# ---------- section mapping ----------
# Maps a tracked link URL to a newsletter section. Update as the template's
# CTA targets evolve. 'open' rows are open-beacons and are skipped.
def section_for(url):
    u = (url or "").lower()
    if u == "open":
        return None
    if "/dashboard/deals" in u:
        return "III · Deal Spotlight"
    if "/dashboard/events" in u:
        return "V · Inside 2^n — Events"
    if "/dashboard/2n-tv" in u or "/2n-tv" in u:
        return "V · Feature — 2^nTV"
    if "/dashboard/amplifier" in u or "/amplifier" in u:
        return "V · Feature — Amplifier"
    if "/dashboard/podcast" in u or "exponential-podcast" in u or "/podcast" in u:
        return "IV · 2^n Intelligence"
    if "/dashboard/feed" in u:
        return "Feed / general"
    if "linkedin.com" in u:
        return "Footer · LinkedIn"
    if u.rstrip("/").endswith("2pwrn.com") or "//2pwrn.com" in u:
        return "Footer · Site"
    if "/dashboard" in u:
        return "Masthead / Home CTA"
    return "Other"

def num(d, k):
    try:
        return int(d.get(k) or 0)
    except (TypeError, ValueError):
        return 0

def pct(a, b):
    return round(a / b * 100, 1) if b else None

def fmt(p):
    return f"{p:.1f}%" if p is not None else "—"

# ---------- pull ----------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    params = urllib.parse.urlencode({
        "filters[name]": "Trends",
        "orders[sdate]": "DESC",
        "limit": 50,
    })
    data = get_json(f"{BASE}/api/3/campaigns?{params}")
    camps = [c for c in data.get("campaigns", []) if str(c.get("status")) == "5"]  # 5 = completed

    editions = []
    for c in camps:
        cid = c.get("id")
        sent = num(c, "send_amt") or num(c, "total_amt")
        uo = num(c, "uniqueopens")
        ulc = num(c, "uniquelinkclicks")
        uns = num(c, "unsubscribes")

        # per-link clicks -> section rollup
        links = get_json(f"{BASE}/api/3/campaigns/{cid}/links").get("links", [])
        sections = {}
        top_link = ("", 0)
        msgid = None
        for L in links:
            msgid = msgid or L.get("messageid")
            sec = section_for(L.get("link"))
            if sec is None:
                continue
            uniq = num(L, "uniquelinkclicks")
            sections[sec] = sections.get(sec, 0) + uniq
            if uniq > top_link[1]:
                top_link = (L.get("link"), uniq)
        top_section = max(sections.items(), key=lambda kv: kv[1]) if sections else ("—", 0)

        # subject line (lives on the message, not the campaign)
        subject = ""
        if msgid:
            try:
                m = get_json(f"{BASE}/api/3/messages/{msgid}")
                subject = (m.get("message") or {}).get("subject", "") or ""
            except Exception:
                subject = ""

        editions.append({
            "campaign_id": cid,
            "name": c.get("name"),
            "send_date": (c.get("sdate") or "")[:10],
            "sent": sent,
            "open_rate": pct(uo, sent),
            "ctr": pct(ulc, sent),
            "ctor": pct(ulc, uo),
            "unsub_rate": pct(uns, sent),
            "top_section": top_section[0],
            "top_link": top_link[0],
            "subject": subject,
            "sections": sections,
            "_uo": uo, "_ulc": ulc, "_uns": uns,
        })

    editions.sort(key=lambda e: e["send_date"])

    # ---------- append-only CSV ledger ----------
    cols = ["campaign_id", "name", "send_date", "sent", "open_rate", "ctr",
            "ctor", "unsub_rate", "top_section", "top_link", "subject", "notes"]
    existing_ids = set()
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            for row in csv.DictReader(f):
                existing_ids.add(str(row.get("campaign_id")))

    new_rows = [e for e in editions if str(e["campaign_id"]) not in existing_ids]
    write_header = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if write_header:
            w.writeheader()
        for e in new_rows:
            w.writerow({
                "campaign_id": e["campaign_id"], "name": e["name"],
                "send_date": e["send_date"], "sent": e["sent"],
                "open_rate": e["open_rate"], "ctr": e["ctr"], "ctor": e["ctor"],
                "unsub_rate": e["unsub_rate"], "top_section": e["top_section"],
                "top_link": e["top_link"], "subject": e["subject"], "notes": "",
            })

    # ---------- digest ----------
    lines = []
    lines.append("# Trends & Topics — Engagement Analytics\n")
    lines.append(f"_Auto-generated by `pull-campaign-analytics.py`. Source: ActiveCampaign REST API. Editions: {len(editions)}._\n")
    lines.append("## Per-edition (chronological)\n")
    lines.append("| Edition | Sent | Open | CTR | CTOR | Unsub | Top section (clicks) |")
    lines.append("|---|--:|--:|--:|--:|--:|---|")
    for e in editions:
        lines.append(f"| {e['name']} | {e['sent']} | {fmt(e['open_rate'])} | {fmt(e['ctr'])} "
                     f"| {fmt(e['ctor'])} | {fmt(e['unsub_rate'])} | {e['top_section']} ({e['top_section'] and e['sections'].get(e['top_section'],0)}) |")
    lines.append("")

    # cross-series section ranking
    agg = {}
    for e in editions:
        for sec, n in e["sections"].items():
            agg[sec] = agg.get(sec, 0) + n
    lines.append("## Cross-series section clicks (sum of unique clicks, all editions)\n")
    lines.append("| Section | Total unique clicks |")
    lines.append("|---|--:|")
    for sec, n in sorted(agg.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {sec} | {n} |")
    lines.append("")

    # takeaway
    by_ctor = sorted([e for e in editions if e["ctor"] is not None], key=lambda e: -e["ctor"])
    ranked = sorted(agg.items(), key=lambda kv: -kv[1])
    lines.append("## Takeaway (read before composing)\n")
    if by_ctor:
        best, worst = by_ctor[0], by_ctor[-1]
        lines.append(f"- **Best edition by CTOR:** {best['name']} ({fmt(best['ctor'])}). "
                     f"**Worst:** {worst['name']} ({fmt(worst['ctor'])}).")
    if ranked:
        top3 = ", ".join(f"{s} ({n})" for s, n in ranked[:3])
        bot3 = ", ".join(f"{s} ({n})" for s, n in ranked[-3:])
        lines.append(f"- **Highest-click sections:** {top3}.")
        lines.append(f"- **Lowest-click sections:** {bot3}.")
    # unsub watch
    uns_sorted = sorted([e for e in editions if e["unsub_rate"] is not None], key=lambda e: -e["unsub_rate"])
    if uns_sorted and uns_sorted[0]["unsub_rate"]:
        lines.append(f"- **Unsub watch:** highest was {uns_sorted[0]['name']} at {fmt(uns_sorted[0]['unsub_rate'])}.")
    lines.append("- **Caveat:** open rates are inflated by Apple Mail Privacy Protection auto-opens — trust CTR/CTOR over open rate, and treat any single month as a weak signal (n ≈ 150–200).")
    lines.append("")

    with open(MD_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"Editions processed : {len(editions)}")
    print(f"New ledger rows    : {len(new_rows)} (existing {len(existing_ids)})")
    print(f"CSV  -> {CSV_PATH}")
    print(f"MD   -> {MD_PATH}\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
