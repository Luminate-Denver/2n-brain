#!/usr/bin/env python3
"""
(Re)build assets/base-plate.png from a shipped episode thumbnail.

The base plate is any episode JPG with the gold band wiped to a clean, empty
solid-gold rectangle. Everything above the band (background, wordmark, hosts,
"PRESENTED BY 2^n") is preserved pixel-for-pixel — that's the constant that
every episode shares.

Only re-run this if the source design above the band ever changes. Point it at
the newest episode that has the desired look.

  python3 make_base_plate.py --src ".../Exponential-Thumbnail-E9.jpg"
"""
import argparse
import os
from PIL import Image, ImageDraw

BAND_TOP, BAND_BOTTOM = 3088, 4072
GOLD = (166, 122, 51)
CANVAS = (8000, 4500)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="source episode .jpg (8000x4500)")
    ap.add_argument("--out", default=None, help="output PNG (defaults to skill asset)")
    args = ap.parse_args()

    out = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "base-plate.png")

    img = Image.open(args.src).convert("RGB")
    if img.size != CANVAS:
        raise SystemExit(f"source must be {CANVAS}, got {img.size}")
    ImageDraw.Draw(img).rectangle([0, BAND_TOP, CANVAS[0], BAND_BOTTOM], fill=GOLD)
    img.save(out)
    print(f"wrote {out}")
