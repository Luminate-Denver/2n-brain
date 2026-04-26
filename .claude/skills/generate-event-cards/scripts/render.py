#!/usr/bin/env python3
"""
Render 2N event table cards or name badges from a manifest JSON.

Usage:
    python render.py --manifest <path> --type table-cards|name-badges --out <pdf>

Manifest schema: see SKILL.md.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
import sys
from pathlib import Path

import qrcode
from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[4]
ASSETS = REPO_ROOT / "assets"

BRAND_GOLD = "#B8870A"
NAME_NAVY = "#0A1A3A"

ASSET_FILES = {
    "two_n_brand":      ASSETS / "2^n_Logo_withCircle_transparent-V2.png",
    "two_n_mini":       ASSETS / "2^n_Logo_v2.svg",
    "silver_check":     ASSETS / "Silver-Check-1.png",
    "gold_check":       ASSETS / "Gold-Check-1.png",
    "founding_caret":   ASSETS / "Founding-Member-Caret-Icon.png",
}


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def qr_data_uri(url: str) -> str:
    qr = qrcode.QRCode(version=None, box_size=10, border=0,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def load_assets() -> dict[str, str]:
    out = {}
    for key, p in ASSET_FILES.items():
        if not p.exists():
            print(f"[warn] missing asset: {p}", file=sys.stderr)
            out[key] = ""
        else:
            out[key] = data_uri(p)
    return out


def pre_name_icons_html(guest: dict, assets: dict[str, str]) -> str:
    """Founding caret first, then silver/gold check (caret sits left of check).

    Uses CSS background-image (instead of an <img>) so the icon is rendered
    as a fixed square box with `background-size: contain`. This locks the
    icon's aspect ratio regardless of how flex layout distributes space
    around it.
    """
    parts = []
    if guest.get("memberStatus") == "Founding Member":
        parts.append(
            f'<span class="pre-icon" style="background-image:url({assets["founding_caret"]})"></span>'
        )
    amp = (guest.get("amplifierStatus") or "").lower()
    if amp == "silver":
        parts.append(
            f'<span class="pre-icon" style="background-image:url({assets["silver_check"]})"></span>'
        )
    elif amp == "gold":
        parts.append(
            f'<span class="pre-icon" style="background-image:url({assets["gold_check"]})"></span>'
        )
    return "".join(parts)


def title_text(guest: dict) -> str | None:
    if guest.get("titleOverride"):
        return guest["titleOverride"]
    ms = guest.get("memberStatus")
    if ms in ("Founding Member", "Member"):
        return ms
    return None


def sponsor_logos_html(sponsors: list[dict], manifest_dir: Path, *, badge: bool = False) -> str:
    slot_cls = "sponsor-slot sponsor-slot--badge" if badge else "sponsor-slot"
    tags = []
    for s in sponsors:
        uri = data_uri(manifest_dir / s["logoPath"])
        tags.append(f'<div class="{slot_cls}"><img class="sponsor-logo" src="{uri}" alt=""/></div>')
    return "".join(tags)


def sponsor_qr_cells_html(sponsors: list[dict], manifest_dir: Path) -> str:
    cells = []
    for s in sponsors:
        logo = data_uri(manifest_dir / s["logoPath"])
        qr = qr_data_uri(s["website"])
        cells.append(
            f'<div class="qr-cell">'
            f'  <img class="qr" src="{qr}" alt=""/>'
            f'  <img class="sponsor-logo" src="{logo}" alt=""/>'
            f'</div>'
        )
    return "".join(cells)


def table_card_pages(guest: dict, sponsors_html: str, qr_row_html: str, assets: dict[str, str]) -> str:
    icons = pre_name_icons_html(guest, assets)
    t = title_text(guest)
    status = ""
    if t:
        status = (
            f'<div class="status">'
            f'  <img class="mini-2n" src="{assets["two_n_mini"]}" alt=""/>'
            f'  <span>{t}</span>'
            f'</div>'
        )
    company = guest.get("company") or ""
    n = len(guest["name"])
    if n <= 15:
        name_class = "name"
    elif n <= 19:
        name_class = "name name--mid"
    else:
        name_class = "name name--long"

    icons_block = f'<span class="pre-icons">{icons}</span>' if icons else ""
    front = f'''
      <section class="page card-front">
        <div class="stack">
          <img class="brand" src="{assets["two_n_brand"]}" alt=""/>
          <div class="name-row">
            <h1 class="{name_class}">{icons_block}{guest["name"]}</h1>
          </div>
          {status}
          <div class="company">{company}</div>
          <div class="sponsors">{sponsors_html}</div>
        </div>
      </section>
    '''
    back = f'''
      <section class="page card-back">
        <div class="qr-row">{qr_row_html}</div>
      </section>
    '''
    return front + back


def name_badge_page(guest: dict, sponsors_html: str, assets: dict[str, str]) -> str:
    icons = pre_name_icons_html(guest, assets)
    t = title_text(guest)
    status = ""
    if t:
        status = (
            f'<div class="status">'
            f'  <img class="mini-2n" src="{assets["two_n_mini"]}" alt=""/>'
            f'  <span>{t}</span>'
            f'</div>'
        )
    company = guest.get("company") or ""
    name_class = "name" if len(guest["name"]) <= 22 else "name name--long"


    icons_block = f'<span class="pre-icons">{icons}</span>' if icons else ""
    return f'''
      <section class="page badge">
        <div class="stack">
          <img class="brand" src="{assets["two_n_brand"]}" alt=""/>
          <div class="name-row">
            <h1 class="{name_class}">{icons_block}{guest["name"]}</h1>
          </div>
          {status}
          <div class="company">{company}</div>
          <div class="sponsors">{sponsors_html}</div>
        </div>
      </section>
    '''


TABLE_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap');
@page {{ size: 6in 4in; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; font-family: 'Overused Grotesk', 'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif; color: #111; }}
.page {{
  width: 6in; height: 4in; page-break-after: always;
  position: relative; background: #fff;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 0.3in 0.4in;
  text-align: center;
}}
.page:last-child {{ page-break-after: auto; }}
.card-front .stack {{
  display: flex; flex-direction: column; align-items: center;
  width: 100%;
}}
.card-front .brand {{ height: 0.55in; }}
.name-row {{
  width: 100%;
  text-align: center;
  margin-top: 0.18in;
}}
.name {{
  display: inline-block;
  position: relative;
  color: {NAME_NAVY};
  font-size: 40pt; font-weight: 400; letter-spacing: -0.07rem;
  margin: 0; line-height: 1.05; text-align: center;
}}
.name--mid {{ font-size: 36pt; }}
.name--long {{ font-size: 32pt; }}
.pre-icons {{
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(calc(-50% + 0.032in));
  margin-right: 0.1in;
  display: flex;
  align-items: center;
  gap: 0.08in;
}}
.pre-icon {{
  display: inline-block;
  height: 0.245in; width: 0.245in;
  min-width: 0.245in; max-width: 0.245in;
  min-height: 0.245in; max-height: 0.245in;
  flex-shrink: 0; flex-grow: 0;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}}
.status {{
  display: inline-flex; align-items: center; gap: 0.07in;
  color: {BRAND_GOLD}; font-size: 14pt; font-weight: 400;
  margin-top: 0.03in;
}}
.status .mini-2n {{ height: 0.22in; }}
.company {{
  font-family: 'Instrument Serif', 'Times New Roman', Georgia, serif;
  color: {BRAND_GOLD}; font-size: 22pt; font-weight: 400;
  margin-top: 0.25in; text-align: center;
}}
.sponsors {{
  margin-top: 0.35in;
  display: flex; align-items: center; justify-content: center; gap: 0.5in;
}}
.sponsor-slot {{
  width: 1.4in; height: 0.55in;
  display: flex; align-items: center; justify-content: center;
}}
.sponsor-logo {{
  max-width: 100%; max-height: 100%;
  object-fit: contain; filter: brightness(0) invert(20%);
}}

/* back */
.card-back {{ justify-content: center; padding: 0.3in; }}
.qr-row {{
  display: flex; align-items: center; justify-content: center; gap: 0.7in;
}}
.qr-cell {{ display: flex; flex-direction: column; align-items: center; gap: 0.15in; }}
.qr {{ height: 1.3in; width: 1.3in; }}
.qr-cell .sponsor-logo {{ width: 1.2in; height: 0.45in; max-width: 1.2in; max-height: 0.45in; }}
"""

BADGE_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap');
@page {{ size: 3.5in 2in; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; font-family: 'Overused Grotesk', 'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif; color: #111; }}
.page.badge {{
  width: 3.5in; height: 2in; page-break-after: always;
  position: relative; background: #fff;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 0.1in 0.2in;
  text-align: center;
}}
.page.badge:last-child {{ page-break-after: auto; }}
.badge .stack {{
  display: flex; flex-direction: column; align-items: center;
  width: 100%;
}}
.badge .brand {{ height: 0.28in; }}
.badge .name-row {{ width: 100%; text-align: center; margin-top: 0.06in; }}
.badge .name {{
  display: inline-block;
  position: relative;
  color: {NAME_NAVY};
  font-size: 22pt; font-weight: 400; margin: 0; line-height: 1.05;
  letter-spacing: -0.038rem; text-align: center;
}}
.badge .name--long {{ font-size: 18pt; }}
.badge .pre-icons {{
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(calc(-50% + 0.024in));
  margin-right: 0.05in;
  display: flex;
  align-items: center;
  gap: 0.04in;
}}
.badge .pre-icon {{
  display: inline-block;
  height: 0.11in; width: 0.11in;
  min-width: 0.11in; max-width: 0.11in;
  min-height: 0.11in; max-height: 0.11in;
  flex-shrink: 0; flex-grow: 0;
  background-size: 100% 100%;
  background-repeat: no-repeat;
  background-position: center;
}}
.badge .status {{
  display: inline-flex; align-items: center; gap: 0.04in;
  color: {BRAND_GOLD}; font-size: 8pt; margin-top: 0.015in;
}}
.badge .status .mini-2n {{ height: 0.12in; }}
.badge .company {{
  font-family: 'Instrument Serif', 'Times New Roman', Georgia, serif;
  color: {BRAND_GOLD}; font-size: 12pt; margin-top: 0.10in; text-align: center;
}}
.badge .sponsors {{
  margin-top: 0.14in;
  display: flex; align-items: center; justify-content: center; gap: 0.2in;
}}
.badge .sponsor-slot {{
  width: 0.65in; height: 0.26in;
  display: flex; align-items: center; justify-content: center;
}}
.badge .sponsor-logo {{
  max-width: 100%; max-height: 100%;
  object-fit: contain; filter: brightness(0) invert(20%);
}}
"""


def build_html(manifest: dict, manifest_dir: Path, kind: str, assets: dict[str, str]) -> str:
    sponsors = manifest["sponsors"]
    guests = manifest["guests"]

    if kind == "table-cards":
        css = TABLE_CSS
        s_html = sponsor_logos_html(sponsors, manifest_dir)
        qr_row = sponsor_qr_cells_html(sponsors, manifest_dir)
        body_parts = [table_card_pages(g, s_html, qr_row, assets) for g in guests]
    elif kind == "name-badges":
        css = BADGE_CSS
        s_html = sponsor_logos_html(sponsors, manifest_dir, badge=True)
        body_parts = [name_badge_page(g, s_html, assets) for g in guests]
    else:
        raise ValueError(f"unknown kind: {kind}")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>{"".join(body_parts)}</body></html>"""


def render_pdf(html: str, out: Path, kind: str) -> None:
    width, height = ("6in", "4in") if kind == "table-cards" else ("3.5in", "2in")
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.pdf(
            path=str(out),
            width=width,
            height=height,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--type", required=True, choices=["table-cards", "name-badges"])
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    manifest_dir = args.manifest.resolve().parent
    assets = load_assets()
    html = build_html(manifest, manifest_dir, args.type, assets)

    debug_html = args.out.with_suffix(".html")
    debug_html.write_text(html)

    render_pdf(html, args.out, args.type)
    print(f"wrote {args.out}  ({len(manifest['guests'])} guests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
