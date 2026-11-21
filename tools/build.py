#!/usr/bin/env python3
"""Turn the generator's raw images into upscaled panels for tools/panorama.py.

    uv run --no-project --with numpy --with pillow --with opencv-python-headless \
        python -I tools/build.py [NN-slug ...]

For each scene with images in work/raw/:

    NN-slug.png        -> work/panels/NN-slug/main.webp      3840 x 2160
    NN-slug-right.png  -> work/panels/NN-slug/right.webp     3840 x 2160
    NN-slug-left.png   -> work/panels/NN-slug/left.webp      2160 x 3840

The panels are not shipped on their own: tools/panorama.py stitches them with
the wider raw panels and surroundings into one seamless 9840 x 3840 wallpaper
per scene, backgrounds/NN-slug.webp.

The side panels were painted around a strip of the main image (see
tools/span-canvas.py). Each is aligned to that strip by feature matching, its
colour matched to the strip, then cut to its target rectangle. Upscaling
blends Real-ESRGAN (realesrgan-x4plus) with a plain Lanczos enlargement, 65/35,
like Farbenlehre's wallpapers.
"""
import hashlib, subprocess, sys, tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW, CANVAS, WORK = ROOT / "work/raw", ROOT / "work/canvas", ROOT / "work"
ESRGAN = WORK / "bin/realesrgan/realesrgan-ncnn-vulkan"
UPSCALED = WORK / "upscaled"
PANELS = WORK / "panels"
ESRGAN_SHARE = 0.65
QUALITY = 92

# The span layout in logical units (see tools/span-canvas.py).
#   left   x 0..1080,    y 0..1920
#   center x 1080..3000, y 480..1560
#   right  x 3000..4920, y 550..1630
# Each canvas covers a known window of it:
#   right canvas: x 2520..4920, y 345..1695
#   left canvas:  x 0..1560,    y -150..2190


def load(path):
    return np.asarray(Image.open(path).convert("RGB"))


def esrgan(img, key):
    """4x Real-ESRGAN of an RGB array, cached under work/upscaled/ by name and content."""
    UPSCALED.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(np.ascontiguousarray(img).tobytes()).hexdigest()[:10]
    out = UPSCALED / f"{key}-{digest}.png"
    if not out.exists():
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.png"
            Image.fromarray(img).save(src)
            subprocess.run([str(ESRGAN), "-i", str(src), "-o", str(out),
                            "-n", "realesrgan-x4plus", "-t", "64"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return load(out)


def upscale(img, size, key):
    big = Image.fromarray(esrgan(img, key)).resize(size, Image.LANCZOS)
    plain = Image.fromarray(img).resize(size, Image.LANCZOS)
    mixed = ESRGAN_SHARE * np.asarray(big, np.float32) + (1 - ESRGAN_SHARE) * np.asarray(plain, np.float32)
    return np.clip(mixed + 0.5, 0, 255).astype(np.uint8)


def save_webp(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(path, "WEBP", quality=QUALITY, method=6)
    print(f"  {path.relative_to(ROOT)}  {img.shape[1]}x{img.shape[0]}  {path.stat().st_size / 1e6:.2f} MB")


def strip_rect(side, w, h):
    """Where tools/span-canvas.py put the main image's strip, in canvas px."""
    strip = round(w * 480 / 1920)
    if side == "right":
        return 0, round(h * 0.1), round(strip * 0.8), round(h * 0.8)
    k = 1024 / 1560
    return round(1080 * k), round(630 * k), 1024 - round(1080 * k), round(1080 * k)


def screen_rect(side, cw, ch):
    """The part of a canvas its screen shows, in canvas px (x, y, w, h)."""
    if side == "right":
        k = cw / 2400
        return round(480 * k), round(205 * k), cw - round(480 * k), round(1080 * k)
    k = cw / 1560
    return 0, round(150 * k), round(1080 * k), round(1920 * k)


def align(out, canvas, rect, with_matrix=False):
    """Warp the generated image onto the canvas so its copy of the strip lies on the original.

    With `with_matrix`, also return the 2x3 warp, so a caller can tell the
    generated pixels from the replicated border the warp leaves at the edges.
    """
    x, y, w, h = rect
    if out.shape[:2] != canvas.shape[:2]:
        print(f"  generator returned {out.shape[1]}x{out.shape[0]}, canvas is {canvas.shape[1]}x{canvas.shape[0]}: resizing")
        out = cv2.resize(out, (canvas.shape[1], canvas.shape[0]), interpolation=cv2.INTER_LANCZOS4)
    gray = lambda a: cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    mask = np.zeros(canvas.shape[:2], np.uint8)
    mask[y + 4:y + h - 4, x + 4:x + w - 4] = 255
    # Search the generated image around the strip, generously.
    near = np.zeros(canvas.shape[:2], np.uint8)
    pad = max(w, h) // 3
    near[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 255
    # Space is mostly black, so look for faint features too.
    sift = cv2.SIFT_create(4000, contrastThreshold=0.01)
    kc, dc = sift.detectAndCompute(gray(canvas), mask)
    ko, do = sift.detectAndCompute(gray(out), near)
    matrix, inliers = None, 0
    if dc is not None and do is not None and len(kc) >= 8 and len(ko) >= 8:
        pairs = cv2.BFMatcher().knnMatch(do, dc, k=2)
        good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n.distance]
        if len(good) >= 8:
            src = np.float32([ko[m.queryIdx].pt for m in good])
            dst = np.float32([kc[m.trainIdx].pt for m in good])
            matrix, keep = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.0)
            inliers = int(keep.sum()) if keep is not None else 0
    scale = float(np.hypot(*matrix[0, :2])) if matrix is not None else 0.0
    # The generator keeps the strip roughly where it was; anything far off is a false match.
    plausible = (matrix is not None and inliers >= 8 and 0.85 <= scale <= 1.15
                 and abs(matrix[0, 2]) < 0.1 * canvas.shape[1] + 80 and abs(matrix[1, 2]) < 0.1 * canvas.shape[0] + 80)
    if plausible:
        print(f"  alignment: {inliers} matches, shift {matrix[0, 2]:+.1f},{matrix[1, 2]:+.1f} px, scale {scale:.4f}")
    else:
        # Too few features: find the shift of the strip as a whole.
        a = np.float32(gray(canvas)[y:y + h, x:x + w])
        b = np.float32(gray(out)[y:y + h, x:x + w])
        (dx, dy), response = cv2.phaseCorrelate(b, a, cv2.createHanningWindow((w, h), cv2.CV_32F))
        if response > 0.05 and abs(dx) < 40 and abs(dy) < 40:
            print(f"  alignment: {inliers} matches, strip correlation {response:.2f}, shift {dx:+.1f},{dy:+.1f} px")
            matrix = np.float32([[1, 0, dx], [0, 1, dy]])
        else:
            print(f"  alignment: {inliers} matches, weak correlation {response:.2f}, keeping the generator's placement")
            matrix = np.float32([[1, 0, 0], [0, 1, 0]])
    aligned = cv2.warpAffine(out, matrix, (canvas.shape[1], canvas.shape[0]),
                             flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    return (aligned, matrix) if with_matrix else aligned


SEAM = 16  # strip columns next to the seam, in canvas px


def seam_profile(img, rect, side):
    """Mean of each row over the strip's columns next to the seam, per channel."""
    x, y, w, h = rect
    cols = slice(x + w - SEAM, x + w) if side == "right" else slice(x, x + SEAM)
    return img[y:y + h, cols].astype(np.float32).mean(axis=1)


def match_colour(aligned, canvas, rect, side):
    """A brightness gain that brings the generated image to the original's at the seam.

    Measured only in the strip columns next to the seam, row by row, since
    that is what the eye compares across the bezel; the generator often
    repaints the rest of the strip, such as a bright disk, a little
    differently. One gain for all three channels keeps hues, and no offset
    keeps black space black. The gain is kept mild and used only if it
    brings the seam clearly closer to the original.
    """
    luma = np.float32([0.2126, 0.7152, 0.0722])
    ref = seam_profile(canvas, rect, side) @ luma
    got = seam_profile(aligned, rect, side) @ luma
    gain = float(np.clip((ref * got).sum() / max(float((got * got).sum()), 1e-6), 0.85, 1.18))
    before, after = np.abs(got - ref).mean(), np.abs(got * gain - ref).mean()
    if after > before * 0.9 or before - after < 0.5:
        print(f"  colour: kept as generated (seam difference {before:.1f})")
        return aligned
    print(f"  colour: brightness x{gain:.2f} (seam difference {before:.1f} -> {after:.1f})")
    return np.clip(aligned.astype(np.float32) * gain + 0.5, 0, 255).astype(np.uint8)


def leftover_gray(img, rect):
    """Share of the shown area that is still the flat #808080 canvas."""
    x, y, w, h = rect
    part = img[y:y + h, x:x + w].astype(np.int16)
    flat = (np.abs(part - 128) <= 3).all(axis=2)
    return float(flat.mean())


def build_side(slug, side):
    raw = RAW / f"{slug}-{side}.png"
    canvas_path = CANVAS / f"{slug}-{side}-canvas.png"
    if not raw.exists() or not canvas_path.exists():
        print(f"  {side}: missing {raw.name if not raw.exists() else canvas_path.name}, skipped")
        return None
    main = load(RAW / f"{slug}.png")
    canvas, out = load(canvas_path), load(raw)
    rect = strip_rect(side, main.shape[1], main.shape[0])
    aligned = match_colour(align(out, canvas, rect), canvas, rect, side)
    x, y, w, h = screen_rect(side, canvas.shape[1], canvas.shape[0])
    gray = leftover_gray(aligned, (x, y, w, h))
    if gray > 0.002:
        print(f"  WARNING: {gray:.1%} of the {side} screen is still gray canvas")
    shown = np.ascontiguousarray(aligned[y:y + h, x:x + w])
    size = (3840, 2160) if side == "right" else (2160, 3840)
    img = upscale(shown, size, f"{slug}-{side}")
    save_webp(img, PANELS / slug / f"{side}.webp")
    return img


def build(slug):
    print(slug)
    main = load(RAW / f"{slug}.png")
    print(f"  main {main.shape[1]}x{main.shape[0]}")
    center = upscale(main, (3840, 2160), slug)
    save_webp(center, PANELS / slug / "main.webp")
    build_side(slug, "left")
    build_side(slug, "right")


if __name__ == "__main__":
    slugs = sys.argv[1:] or sorted(p.stem for p in RAW.glob("[0-9][0-9]-*.png")
                                   if not p.stem.endswith(("-left", "-right")))
    for slug in slugs:
        build(slug)
