#!/usr/bin/env python3
"""
Render an Exponential podcast episode thumbnail (8000x4500) by typing the gold
bottom band's two text lines onto a constant base plate.

Everything above the band (background texture, "PRESENTED BY 2^n", the
"Exponential" wordmark, and "with Kyle Shoemaker & Brett Kaplan") lives in the
base plate and is reused pixel-for-pixel. Only the title + subtitle change per
episode.

The two band lines are rendered with **system Chrome** (Overused Grotesk Roman,
embedded as a data-URL) so that pair kerning + CSS letter-spacing match
InDesign's spacing model. The transparent text layer is then composited onto the
base plate with PIL, leaving the background untouched. All constants were
reverse-engineered from the shipped E1-E9 thumbnails (see SKILL.md "Calibration").
"""
import argparse
import base64
import io
import os

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

# ---- Locked design constants (measured from E1-E9) -------------------------
CANVAS = (8000, 4500)
BAND_TOP, BAND_BOTTOM = 3088, 4072
GOLD = (166, 122, 51)                         # #A67A33
CENTER_X = 4000
SCALE = 4                                     # device_scale_factor (logical*4 = device px)
VIEW_W = 3000                                 # logical viewport width (12000px device) — wide
                                              # enough that a full-size long title never clips
                                              # during measurement (the canvas is only 8000px)

OTF = "/Users/christopherjames/Library/Fonts/OverusedGrotesk-Roman.otf"

# Title (black). size=cap height ~290px (constant). letter-spacing kept em-constant.
TITLE_SIZE = 440
TITLE_LS_EM = -0.045          # CJ preference (looser than the E9-matched -0.0798)
TITLE_BASELINE = 3577
TITLE_CAP_RATIO = 0.6545                      # baseline = ink_top + ratio*size
TITLE_FILL = "#000000"

# Subtitle (white).
SUB_SIZE = 280
SUB_LS_EM = -0.0528
SUB_BASELINE = 3903
SUB_ASC_RATIO = 0.7036
SUB_FILL = "#ffffff"

# Vertical centering. The title+subtitle are placed as ONE group whose optical
# block (title cap-top → subtitle baseline) stays centered on a fixed axis, so a
# shrunk title doesn't drop and leave a big gap above it — the top and bottom gaps
# grow together. The axis and the title→subtitle leading are taken from E9 at full
# size, so a full-size title reproduces E9 exactly and only shrunk titles re-center.
LEADING = SUB_BASELINE - TITLE_BASELINE                          # 326px, baseline→baseline
GROUP_CENTER = ((TITLE_BASELINE - TITLE_CAP_RATIO * TITLE_SIZE)  # E9 block center = 3596
                + SUB_BASELINE) / 2.0

# Long lines auto-shrink (em-tracking preserved) so they keep a safe side margin
# matching the shipped episodes. 6600px ≈ the average shipped title width
# (E5 6880 / E6 6592 / E7 6489 / E8 6543 / E9 6413 → ~6580), i.e. ~82% of width,
# ~9% margin per side. Normal-length titles fall under this and render at full
# size 440; only over-long titles (like E10) shrink to fit it.
MAX_TEXT_WIDTH = 6600
MIN_SIZE = 280
# ---------------------------------------------------------------------------

_FONTSRC = "url(data:font/otf;base64,%s) format('opentype')" % \
    base64.b64encode(open(OTF, "rb").read()).decode()

_PAGE = """<!doctype html><html><head><meta charset=utf-8><style>
@font-face{font-family:'OG';src:%s;font-weight:400;font-style:normal;}
html,body{margin:0;padding:0;background:transparent;}
#t{position:absolute;left:0;right:0;text-align:center;white-space:nowrap;
   font-family:'OG';font-weight:400;color:%%(color)s;
   font-size:%%(size)spx;letter-spacing:%%(ls)spx;top:40px;line-height:1.5;
   font-kerning:normal;text-rendering:geometricPrecision;}
</style></head><body><span id="t">%%(text)s</span></body></html>""" % _FONTSRC


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Renderer:
    def __init__(self, page):
        self.page = page

    def _draw(self, text, size_dev, ls_dev, color):
        self.page.set_content(_PAGE % {
            "size": size_dev / SCALE, "ls": ls_dev / SCALE,
            "color": color, "text": _esc(text)})
        self.page.wait_for_timeout(60)
        if not self.page.evaluate("()=>document.fonts.check(\"40px 'OG'\")"):
            raise SystemExit("Overused Grotesk failed to load in Chrome")
        self.page.wait_for_timeout(40)
        png = self.page.screenshot(omit_background=True,
                                   clip={"x": 0, "y": 0, "width": VIEW_W, "height": 1125})
        return Image.open(io.BytesIO(png)).convert("RGBA")

    def fit(self, text, base_size, ls_em, color):
        # auto-fit: shrink (em-tracking preserved) until the rendered ink width is
        # within MAX_TEXT_WIDTH. Iterative — one proportional step under-corrects
        # because ink width isn't perfectly linear in size, and the first estimate
        # can be off if measured near the viewport edge. Returns the raw (unplaced)
        # transparent layer + the chosen size.
        size = base_size
        layer = self._draw(text, size, ls_em * size, color)
        x0, x1 = _ink_x(layer)
        for _ in range(8):
            width = x1 - x0
            if width <= MAX_TEXT_WIDTH or size <= MIN_SIZE:
                break
            size = max(MIN_SIZE, int(size * MAX_TEXT_WIDTH / width) - 1)
            layer = self._draw(text, size, ls_em * size, color)
            x0, x1 = _ink_x(layer)
        return layer, size


def _ink_x(layer):
    import numpy as np
    a = np.asarray(layer)
    xs = np.where((a[:, :, 3] > 40).any(axis=0))[0]
    return xs.min(), xs.max()


def _place(layer, size, baseline, ratio):
    import numpy as np
    a = np.asarray(layer)
    m = a[:, :, 3] > 40
    ys, xs = np.where(m)
    cx = (xs.min() + xs.max()) / 2
    dy = int(round(baseline - ratio * size - ys.min()))
    dx = int(round(CENTER_X - cx))
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.paste(layer, (dx, dy), layer)
    return out


def render(title, subtitle, base_path, out_path, quality=95):
    base = Image.open(base_path).convert("RGBA")
    if base.size != CANVAS:
        raise SystemExit(f"base plate must be {CANVAS}, got {base.size}")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": VIEW_W, "height": 1125},
                                device_scale_factor=SCALE)
        r = Renderer(page)
        tlayer_raw, tsize = r.fit(title, TITLE_SIZE, TITLE_LS_EM, TITLE_FILL)
        slayer_raw, ssize = r.fit(subtitle, SUB_SIZE, SUB_LS_EM, SUB_FILL)
        browser.close()

    # Center the title+subtitle group on GROUP_CENTER. title_baseline is solved so
    # the optical block (title cap-top → subtitle baseline) is centered; the
    # subtitle sits LEADING below the title. At full size this reduces to E9's
    # baselines (3577 / 3903); a shrunk title rides up so the gaps stay balanced.
    title_baseline = GROUP_CENTER - (LEADING - TITLE_CAP_RATIO * tsize) / 2.0
    sub_baseline = title_baseline + LEADING
    tlayer = _place(tlayer_raw, tsize, title_baseline, TITLE_CAP_RATIO)
    slayer = _place(slayer_raw, ssize, sub_baseline, SUB_ASC_RATIO)

    comp = Image.alpha_composite(Image.alpha_composite(base, tlayer), slayer).convert("RGB")
    if out_path.lower().endswith((".jpg", ".jpeg")):
        comp.save(out_path, quality=quality, subsampling=0)
    else:
        comp.save(out_path)
    print(f"wrote {out_path}")
    print(f"  title:    size {tsize} baseline {title_baseline:.0f} (em {TITLE_LS_EM}) | {title}")
    print(f"  subtitle: size {ssize} baseline {sub_baseline:.0f} (em {SUB_LS_EM}) | {subtitle}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default=os.path.join(SKILL, "assets", "base-plate.png"))
    args = ap.parse_args()
    render(args.title, args.subtitle, args.base, args.out)
