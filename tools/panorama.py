#!/usr/bin/env python3
"""Assemble each scene into one panorama for spanning wallpaper tools such as Station.

    uv run --no-project --with numpy --with scipy --with pillow --with opencv-python-headless \
        python -I tools/panorama.py [--canvas] [NN-slug ...]

    backgrounds/NN-slug.webp                 the 4K wallpaper (the main screen)
    work/panels/NN-slug/{left,right}.webp    its side panels, cut by build.py
    work/raw/NN-slug-{left,right}.png        the generator's wider panels
    work/raw/NN-slug-gaps.png                the generator's fill for the gaps
    -> backgrounds/span-NN-slug.webp         9840 x 3840, the whole three-screen layout

The layout, in logical pixels, is the one the scenes were painted for:

    left   portrait 1080 x 1920   at x 0,    y 0
    main   16:9     1920 x 1080   at x 1080, y 480
    right  16:9     1920 x 1080   at x 3000, y 550

4920 x 1920 together; the panorama is twice that, the 4K screen's density.
A tool that spans one image across this layout, scaled to cover it, shows
each monitor exactly its crisp wallpaper or panel. Around the monitors the
panorama continues with the generator's wider panels.

Those panels leave strips above and below the main and right screens that
nothing was painted for. `--canvas` writes work/canvas/NN-slug-gaps-canvas.png,
the right 16:9 of the panorama with those strips flat gray, for the image
generator to paint (see work/BRIEF.md). Its result, one consistent painting,
becomes everything around the main and right screens; without one the
panels stay and the strips fade softly from their edges.

The monitors' images and the paintings around them were made separately and
differ a little where they meet. The surroundings are evened out toward the
monitors with a smooth tone correction (a membrane, solved on a coarse grid),
and the monitors' images are joined to them by multi-band blending: fine
detail switches at the monitor's edge, broad tone and haze cross it over
about a hundred pixels. Away from the edges that face the surroundings, each
monitor shows its image exactly.
"""
import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build", ROOT / "tools" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

SCALE = 2                          # panorama pixels per logical pixel
LAYOUT = (4920, 1920)              # logical size of the whole layout
SCREENS = {                        # logical rectangles (x, y, w, h)
    "left": (0, 0, 1080, 1920),
    "main": (1080, 480, 1920, 1080),
    "right": (3000, 550, 1920, 1080),
}
# Where each raw generated panel lies, in logical pixels: its canvas's
# top-left corner and logical width (see tools/span-canvas.py).
RAW = {
    "left": {"origin": (0, -150), "width": 1560},
    "right": {"origin": (2520, 345), "width": 2400},
}
# The gap canvas: the right 16:9 of the layout, which holds every gap, at
# the size the image generator returns for 16:9.
GAP_SIZE = (1672, 941)
GAP_X = LAYOUT[0] - LAYOUT[1] * 16 / 9
GAP_K = GAP_SIZE[0] / (LAYOUT[0] - GAP_X)              # canvas px per logical px
# The main screen's part of the gap canvas, which the alignment matches on.
GAP_ALIGN = (0, round(480 * GAP_K), round((3000 - GAP_X) * GAP_K), round(1080 * GAP_K))
BACKGROUND = (10, 13, 22)          # the theme's background, #0a0d16
GRAY = 128
QUALITY = 88


def px(value):
    return int(round(value * SCALE))


def aligned_raw(slug, side):
    """The generator's panel, aligned and colour-matched onto its canvas as build.py does, and where it is real.

    The alignment moves the panel by a few pixels and repeats its edge into
    the rows or columns it leaves, which are streaks, not painting.
    """
    main = build.load(build.RAW / f"{slug}.png")
    canvas = build.load(build.CANVAS / f"{slug}-{side}-canvas.png")
    out = build.load(build.RAW / f"{slug}-{side}.png")
    rect = build.strip_rect(side, main.shape[1], main.shape[0])
    aligned, matrix = build.align(out, canvas, rect, with_matrix=True)
    real = cv2.warpAffine(np.full(out.shape[:2], 255, np.uint8), matrix, (canvas.shape[1], canvas.shape[0]),
                          flags=cv2.INTER_NEAREST, borderValue=0)
    real = cv2.erode(real, np.ones((5, 5), np.uint8))
    return build.match_colour(aligned, canvas, rect, side), real


def painted(slug):
    """Everything painted for the scene, placed: the wide panels, then the crisp images on the monitors."""
    size = (px(LAYOUT[0]), px(LAYOUT[1]))
    pano = Image.new("RGB", size, BACKGROUND)
    mask = Image.new("L", size, 0)

    for side, raw in RAW.items():
        aligned, real = aligned_raw(slug, side)
        image = Image.fromarray(aligned)
        factor = px(raw["width"]) / image.width
        size_ = (px(raw["width"]), round(image.height * factor))
        image = image.resize(size_, Image.LANCZOS)
        real = Image.fromarray(real).resize(size_, Image.NEAREST)
        box = (px(raw["origin"][0]), px(raw["origin"][1]))
        pano.paste(image, box, real)
        mask.paste(255, box, real)

    crisp = {
        "main": ROOT / "backgrounds" / f"{slug}.webp",
        "left": ROOT / "work" / "panels" / slug / "left.webp",
        "right": ROOT / "work" / "panels" / slug / "right.webp",
    }
    sharp = []
    for name, path in crisp.items():
        x, y, w, h = SCREENS[name]
        image = Image.open(path).convert("RGB")
        if image.size != (px(w), px(h)):
            image = image.resize((px(w), px(h)), Image.LANCZOS)
        sharp.append((image, (px(x), px(y))))
        pano.paste(image, (px(x), px(y)))
        mask.paste(255, (px(x), px(y), px(x + w), px(y + h)))
    return np.array(pano), np.asarray(mask) > 127, sharp


def membrane(image, inside, cell=16, sigma=3):
    """A smooth correction for the pixels outside `inside` that removes the tone step at its border.

    On a grid of `cell`-pixel cells: just outside the border it is the
    difference between the blurred colour inside and the blurred colour
    outside; elsewhere it is the smoothest field that meets those values
    (Laplace's equation, edges of the image free). Returned at full size.
    """
    height, width = inside.shape
    grid = (width // cell, height // cell)
    weight_in = cv2.resize(inside.astype(np.float32), grid, interpolation=cv2.INTER_AREA)
    weight_out = 1 - weight_in
    colour = image.astype(np.float32)
    sum_in = cv2.resize(colour * inside[..., None], grid, interpolation=cv2.INTER_AREA)
    sum_out = cv2.resize(colour * (~inside)[..., None], grid, interpolation=cv2.INTER_AREA)
    blur = lambda a: cv2.GaussianBlur(a, (0, 0), sigma)
    mean_in = blur(sum_in) / np.maximum(blur(weight_in), 1e-4)[..., None]
    mean_out = blur(sum_out) / np.maximum(blur(weight_out), 1e-4)[..., None]

    core = weight_in >= 0.5
    ring = cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~core
    rows, cols = grid[1], grid[0]
    index = -np.ones((rows, cols), np.int64)
    free = ~ring
    index[free] = np.arange(free.sum())
    fixed = np.where(ring[..., None], mean_in - mean_out, 0).astype(np.float64)

    # 5-point Laplacian over the free cells; ring cells are known values.
    entries_r, entries_c, entries_v = [], [], []
    rhs = np.zeros((free.sum(), 3))
    degree = np.zeros(free.sum())
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        y0, y1 = max(0, -dy), rows - max(0, dy)
        x0, x1 = max(0, -dx), cols - max(0, dx)
        here = (slice(y0, y1), slice(x0, x1))
        there = (slice(y0 + dy, y1 + dy), slice(x0 + dx, x1 + dx))
        a, b = index[here], index[there]
        valid = a >= 0
        degree_add = np.zeros(free.sum())
        np.add.at(degree_add, a[valid], 1)
        degree += degree_add
        both = valid & (b >= 0)
        entries_r.append(a[both]); entries_c.append(b[both]); entries_v.append(-np.ones(both.sum()))
        known = valid & (b < 0)
        np.add.at(rhs, a[known], fixed[there][known])
    n = free.sum()
    entries_r.append(np.arange(n)); entries_c.append(np.arange(n)); entries_v.append(degree)
    laplace = coo_matrix((np.concatenate(entries_v), (np.concatenate(entries_r), np.concatenate(entries_c))),
                         shape=(n, n)).tocsc()
    solved = spsolve(laplace, rhs)
    field = fixed.copy()
    field[free] = solved
    return cv2.resize(field.astype(np.float32), (width, height), interpolation=cv2.INTER_LINEAR)


def gap_canvas(slug):
    """The right 16:9 of the panorama at the generator's size, its gaps flat gray."""
    pano, covered, _ = painted(slug)
    x0 = px(GAP_X)
    image = Image.fromarray(pano[:, x0:]).resize(GAP_SIZE, Image.LANCZOS)
    mask = Image.fromarray((covered[:, x0:] * 255).astype(np.uint8)).resize(GAP_SIZE, Image.BILINEAR)
    canvas = np.array(image)
    canvas[np.asarray(mask) < 250] = GRAY
    out = build.CANVAS / f"{slug}-gaps-canvas.png"
    Image.fromarray(canvas).save(out)
    print(f"  {out.relative_to(ROOT)}  {GAP_SIZE[0]}x{GAP_SIZE[1]}")


def edge_fill(pixels, covered):
    """Fade each gap column from the colour at its painted edge into the scene's colour at that edge of the panorama."""
    pixels = pixels.astype(np.float32)
    filled = np.zeros(covered.shape, dtype=bool)
    fade = px(140)
    height, width = covered.shape

    def edge_colour(rows):
        band = pixels[rows][covered[rows]]
        return band.mean(axis=0) if band.size else np.array(BACKGROUND, dtype=np.float32)

    above_colour = edge_colour(slice(0, px(24)))
    below_colour = edge_colour(slice(height - px(24), height))

    def extent(x):
        rows = np.flatnonzero(covered[:, x])
        return (int(rows[0]), int(rows[-1]) + 1) if rows.size else None

    column = 0
    while column < width:
        current = extent(column)
        end = column + 1
        while end < width and extent(end) == current:
            end += 1
        if current:
            top, bottom = current
            if top > 0:
                weight = np.exp(-(top - np.arange(top)) / fade)[:, None, None]
                pixels[:top, column:end] = pixels[top, column:end][None] * weight + above_colour * (1 - weight)
                filled[:top, column:end] = True
            if bottom < height:
                weight = np.exp(-(np.arange(bottom, height) - bottom + 1) / fade)[:, None, None]
                pixels[bottom:, column:end] = pixels[bottom - 1, column:end][None] * weight + below_colour * (1 - weight)
                filled[bottom:, column:end] = True
        column = end
    image = Image.fromarray(np.clip(pixels + 0.5, 0, 255).astype(np.uint8))
    soft = image.filter(ImageFilter.GaussianBlur(px(24)))
    mask = Image.fromarray((filled * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(px(6)))
    return np.array(Image.composite(soft, image, mask))


def multiband(inner, outer, mask, levels=6):
    """Burt and Adelson's blend of two float images: `inner` where mask is 1, each frequency band over its own width."""
    gi, go, gm = [inner], [outer], [mask]
    for _ in range(levels):
        gi.append(cv2.pyrDown(gi[-1]))
        go.append(cv2.pyrDown(go[-1]))
        gm.append(cv2.pyrDown(gm[-1]))
    m = gm[-1][..., None]
    out = m * gi[-1] + (1 - m) * go[-1]
    for k in range(levels - 1, -1, -1):
        size = (gi[k].shape[1], gi[k].shape[0])
        m = gm[k][..., None]
        out = cv2.pyrUp(out, dstsize=size)
        out += m * (gi[k] - cv2.pyrUp(gi[k + 1], dstsize=size))
        out += (1 - m) * (go[k] - cv2.pyrUp(go[k + 1], dstsize=size))
        gi[k + 1] = go[k + 1] = None
    return out


def generated_surroundings(slug, shape):
    """The generator's painting of the gap canvas, aligned, tone-matched and enlarged onto the panorama; None without one.

    It is one consistent painting of everything around the main and right
    screens, so it replaces the panels there, not just the gaps. Plain
    Lanczos, like the panels' parts outside the monitors: it is the edge of
    the frame, and no monitor shows it on the layout.
    """
    raw = build.RAW / f"{slug}-gaps.png"
    if not raw.exists():
        return None
    canvas = build.load(build.CANVAS / f"{slug}-gaps-canvas.png")
    out = build.align(build.load(raw), canvas, GAP_ALIGN)
    # The generator also changes the tone of what it keeps, mostly lifting
    # the darks; map each channel's distribution back onto the canvas's,
    # measured where the canvas is painted.
    painted_part = cv2.erode((np.abs(canvas.astype(np.int16) - GRAY).max(axis=2) > 0).astype(np.uint8),
                             np.ones((9, 9), np.uint8)).astype(bool)
    levels = np.linspace(0, 100, 201)
    mapped = np.empty(out.shape, np.float32)
    for c in range(3):
        got = np.percentile(out[..., c][painted_part], levels)
        ref = np.percentile(canvas[..., c][painted_part], levels)
        got = np.maximum.accumulate(got + np.arange(len(got)) * 1e-6)
        mapped[..., c] = np.interp(out[..., c], got, ref)
    out = np.clip(mapped + 0.5, 0, 255).astype(np.uint8)
    height, width = shape
    x0 = px(GAP_X)
    layer = np.zeros((height, width, 3), np.uint8)
    layer[:, x0:] = np.asarray(Image.fromarray(out).resize((width - x0, height), Image.LANCZOS))
    return layer


def assemble(slug):
    print(slug)
    pano, covered, sharp = painted(slug)
    height, width = covered.shape
    monitors = np.zeros(covered.shape, bool)
    for crisp, (x, y) in sharp:
        monitors[y:y + crisp.height, x:x + crisp.width] = True

    layer = generated_surroundings(slug, covered.shape)
    if layer is not None:
        # Left of the gap canvas, the left panel; from its edge on, the
        # generator's painting, eased in across the strip where both exist.
        x0 = px(GAP_X)
        ramp = np.clip((np.arange(width, dtype=np.float32) - x0) / px(50), 0, 1)
        ramp = (ramp * ramp * (3 - 2 * ramp))[None, :, None]
        surroundings = pano.astype(np.float32) * (1 - ramp) + layer.astype(np.float32) * ramp
        surroundings = np.clip(surroundings + 0.5, 0, 255).astype(np.uint8)
        print("  surroundings: generated")
    else:
        surroundings = np.where(covered[..., None], pano, edge_fill(pano, covered))
        print("  surroundings: panels, gaps faded from the edges (no work/raw/<scene>-gaps.png)")
    # Even the surroundings out toward the monitors' images, then join them.
    reference = surroundings.copy()
    reference[monitors] = pano[monitors]
    outer = surroundings.astype(np.float32) + membrane(reference, monitors)
    del reference, surroundings, layer
    inner = outer.copy()
    inner[monitors] = pano[monitors]
    joined = multiband(inner, outer, monitors.astype(np.float32))
    del inner, outer
    image = Image.fromarray(np.clip(joined + 0.5, 0, 255).astype(np.uint8))
    del joined
    shown = np.asarray(image)[monitors].astype(np.int16) - pano[monitors]
    print(f"  monitors: {100 * (np.abs(shown).max(axis=1) <= 1).mean():.1f} % of pixels exact (within 1 level)")
    out = ROOT / "backgrounds" / f"span-{slug}.webp"
    image.save(out, "WEBP", quality=QUALITY, method=6)
    print(f"  {out.relative_to(ROOT)}  {image.width}x{image.height}  {out.stat().st_size / 1e6:.2f} MB"
          f"  ({100 * (1 - covered.mean()):.1f} % gaps)")


if __name__ == "__main__":
    args = sys.argv[1:]
    canvas_only = "--canvas" in args
    slugs = [a for a in args if a != "--canvas"] or sorted(
        p.stem for p in (ROOT / "backgrounds").glob("[0-9][0-9]-*.webp"))
    for slug in slugs:
        if canvas_only:
            print(slug)
            gap_canvas(slug)
        else:
            assemble(slug)
