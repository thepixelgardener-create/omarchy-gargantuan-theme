#!/usr/bin/env python3
"""Build the two outpainting canvases for a span wallpaper.

Usage: tools/span-canvas.py work/raw/NN-slug.png work/canvas/

The span layout is three screens side by side, in logical units:
  left   portrait 1080 x 1920   (x 0..1080,    y 0..1920)
  center 16:9     1920 x 1080   (x 1080..3000, y 480..1560)  <- the main wallpaper
  right  16:9     1920 x 1080   (x 3000..4920, y 550..1630)

Each canvas carries a strip of the main wallpaper (its outer 480 units, a
quarter of its width) at the correct scale and position; everything else is
flat mid-gray (#808080), the area the image generator paints.

  NN-slug-right-canvas.png  16:9, covers x 2520..4920, y 345..1695 (2400 x 1350)
  NN-slug-left-canvas.png   2:3,  covers x 0..1560,    y -150..2190 (1560 x 2340)
"""
import subprocess, sys
from pathlib import Path

main = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
w, h = map(int, subprocess.check_output(
    ["magick", "identify", "-format", "%w %h", str(main)]).split())
strip = round(w * 480 / 1920)          # main px in the outer quarter

def canvas(name, cw, ch, crop_x, sx, sy, sw, sh):
    dst = out / f"{main.stem}-{name}-canvas.png"
    subprocess.check_call([
        "magick", "-size", f"{cw}x{ch}", "xc:#808080",
        "(", str(main), "-crop", f"{strip}x{h}+{crop_x}+0", "+repage",
        "-resize", f"{sw}x{sh}!", ")",
        "-geometry", f"+{sx}+{sy}", "-composite", "-strip", str(dst)])
    print(dst, f"{cw}x{ch}", f"strip {sw}x{sh} at +{sx}+{sy}")

# right: canvas is 2400 units wide at the main's pixel width -> scale 0.8
s = 0.8
canvas("right", w, h, w - strip, 0, round(h * 0.1), round(strip * s), round(h * s))

# left: 1024 x 1536 covering 1560 x 2340 units
cw, ch = 1024, 1536
k = cw / 1560                           # canvas px per unit
m = w / 1920                            # main px per unit
canvas("left", cw, ch, 0, round(1080 * k), round(630 * k),
       cw - round(1080 * k), round(1080 * k))
