#!/usr/bin/env python3
"""
Rewrite the hosts line ("with Kyle Shoemaker & <co-host>") in the base plate.

The hosts line lives in the constant region above the gold band, as right-aligned
gold text (with a soft drop shadow) over the textured background. To change a
co-host, this erases the current line by copying a clean strip of background over
it, then redraws the new line with the matching font / gold / shadow / position.

  python3 update_hosts.py --hosts "with Kyle Shoemaker & Matt Burskey"

It backs up the current base plate to assets/base-plate-prev.png and writes the
new one to assets/base-plate.png. All geometry constants were measured from the
shipped E1-E9 thumbnails and are locked.
"""
import argparse
import base64
import io
import os

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
ASSETS = os.path.join(SKILL, "assets")
OTF = "/Users/christopherjames/Library/Fonts/OverusedGrotesk-Roman.otf"

# ---- Locked hosts-line constants (measured from E1-E9) ---------------------
SCALE = 4
GOLD = "#A67A33"
SIZE = 344                      # device px
LS = -23.6                      # device px letter-spacing (em -0.0686)
BASELINE = 2556                 # device y
CAP_RATIO = 0.6545
INK_RIGHT = 6991                # right-aligned to the wordmark's right edge
SHADOW = f"{5/SCALE}px {8/SCALE}px {10/SCALE}px rgba(0,0,0,0.22)"
INPAINT_ROWS = (2316, 2632)     # text + shadow band to wipe
INPAINT_COLS = (2350, 7160)
CLEAN_SRC_TOP = 2690            # clean background strip copied over the line
# ---------------------------------------------------------------------------

_B64 = base64.b64encode(open(OTF, "rb").read()).decode()
_PAGE = """<!doctype html><html><head><meta charset=utf-8><style>
@font-face{font-family:'OG';src:url(data:font/otf;base64,%s) format('opentype');font-weight:400;}
html,body{margin:0;padding:0;background:transparent;}
#t{position:absolute;left:0;right:0;text-align:center;white-space:nowrap;
   font-family:'OG';font-weight:400;color:%%(color)s;
   font-size:%%(size)spx;letter-spacing:%%(ls)spx;top:60px;line-height:1.8;
   font-kerning:normal;text-rendering:geometricPrecision;text-shadow:%%(sh)s;}
</style></head><body><span id="t">%%(text)s</span></body></html>""" % _B64


def _copy_strip_inpaint(img):
    a = np.asarray(img.convert("RGB")).copy()
    ty0, ty1 = INPAINT_ROWS
    x0, x1 = INPAINT_COLS
    sy0 = CLEAN_SRC_TOP
    src = a[sy0:sy0 + (ty1 - ty0), x0:x1].astype(float)
    dst = a[ty0:ty1, x0:x1].astype(float)
    out = src.copy()
    f = 14
    for i in range(f):                       # feather seams into existing bg
        w = i / f
        out[i] = w * src[i] + (1 - w) * dst[i]
        out[-1 - i] = w * src[-1 - i] + (1 - w) * dst[-1 - i]
    a[ty0:ty1, x0:x1] = np.clip(out, 0, 255).astype("uint8")
    return Image.fromarray(a)


def main(hosts):
    base = Image.open(os.path.join(ASSETS, "base-plate.png")).convert("RGB")
    if base.size != (8000, 4500):
        raise SystemExit("base plate must be 8000x4500")
    base.save(os.path.join(ASSETS, "base-plate-prev.png"))
    plate = _copy_strip_inpaint(base)

    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome")
        pg = br.new_page(viewport={"width": 2000, "height": 1200}, device_scale_factor=SCALE)
        pg.set_content(_PAGE % {"size": SIZE / SCALE, "ls": LS / SCALE, "color": GOLD,
                                "sh": SHADOW, "text": hosts.replace("&", "&amp;")})
        pg.wait_for_timeout(80)
        if not pg.evaluate("()=>document.fonts.check(\"40px 'OG'\")"):
            raise SystemExit("Overused Grotesk failed to load in Chrome")
        pg.wait_for_timeout(40)
        png = pg.screenshot(omit_background=True,
                            clip={"x": 0, "y": 0, "width": 2000, "height": 1200})
        br.close()
    layer = Image.open(io.BytesIO(png)).convert("RGBA")

    a = np.asarray(layer)
    m = a[:, :, 3] > 200                      # solid text core (ignore soft shadow) for placement
    ys, xs = np.where(m)
    dy = int(round(BASELINE - CAP_RATIO * SIZE - ys.min()))
    dx = int(round(INK_RIGHT - xs.max()))
    canvas = Image.new("RGBA", (8000, 4500), (0, 0, 0, 0))
    canvas.paste(layer, (dx, dy), layer)
    out = Image.alpha_composite(plate.convert("RGBA"), canvas).convert("RGB")
    out.save(os.path.join(ASSETS, "base-plate.png"))
    print(f"base plate updated: {hosts}")
    print(f"  backup: {os.path.join(ASSETS, 'base-plate-prev.png')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", required=True,
                    help='Full hosts line, e.g. "with Kyle Shoemaker & Matt Burskey"')
    main(ap.parse_args().hosts)
