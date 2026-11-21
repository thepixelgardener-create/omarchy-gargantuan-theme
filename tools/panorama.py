#!/usr/bin/env python3
"""Assemble each scene into one seamless 9840 x 3840 panoramic wallpaper.

    uv run --no-project --with numpy --with scipy --with pillow --with opencv-python-headless \
        python -I tools/panorama.py [--canvas] [NN-slug ...]

    work/panels/NN-slug/{main,left,right}.webp   upscaled crisp panels from build.py
    work/raw/NN-slug-{left,right}.png            wider generated panels (including overlaps)
    work/raw/NN-slug-gaps.png                    generated fill for the top/bottom surroundings
    -> backgrounds/NN-slug.webp                  9840 x 3840 seamless panoramic wallpaper

Each scene is composed across a 4920 x 1920 logical canvas at 2x density
(9840 x 3840):

    left   1080 x 1920   at x 0,    y 0
    main   1920 x 1080   at x 1080, y 480
    right  1920 x 1080   at x 3000, y 550

Each side panel was painted outward around a 480-logical-px overlap strip of
the main scene. Rather than cutting sharply at the panel edges, this script:

1. Places each upscaled panel on its wider generated layer, feathering the
   24-pixel inner edge to avoid sub-pixel rounding steps.
2. Runs a two-pass coarse-to-fine smooth optical-flow alignment inside each
   overlap so horizons, planetary limbs, rings and disks register cleanly,
   decaying smoothly across the side panel.
3. Matches each side panel's exposure and colour smoothly to the main image
   (multiplicative gain plus a dark-gated residual bias so deep black space
   stays dark), fading out across the side panel.
4. Finds a minimum-error seam through each overlap corridor and joins main to
   the side panels with a 7-level multi-band (Laplacian pyramid) blend.
5. Joins the unified panorama seamlessly into the generated top/bottom
   surroundings with a harmonic tone correction (membrane) and 6-level
   multi-band blend.
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
LAYOUT = (4920, 1920)              # logical size of the whole canvas
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
# The gap canvas: the right 16:9 of the canvas, which holds every gap, at
# the size the image generator returns for 16:9.
GAP_SIZE = (1672, 941)
GAP_X = LAYOUT[0] - LAYOUT[1] * 16 / 9
GAP_K = GAP_SIZE[0] / (LAYOUT[0] - GAP_X)              # canvas px per logical px
# The main panel's part of the gap canvas, which the alignment matches on.
GAP_ALIGN = (0, round(480 * GAP_K), round((3000 - GAP_X) * GAP_K), round(1080 * GAP_K))
BACKGROUND = (10, 13, 22)          # the theme's background, #0a0d16
GRAY = 128
QUALITY = 88


def px(value):
    return int(round(value * SCALE))


def main_panel_path(slug):
    """Source 4K main panel: work/panels/<slug>/main.webp."""
    path = ROOT / "work" / "panels" / slug / "main.webp"
    if path.exists():
        return path
    raise FileNotFoundError(f"missing main panel {path.relative_to(ROOT)} (run tools/build.py first)")


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


def side_layer(slug, side, shape):
    """One side panel at panorama scale: wider aligned_raw with the crisp upscaled panel feathered in."""
    height, width = shape
    aligned, real = aligned_raw(slug, side)
    raw_cfg = RAW[side]
    image = Image.fromarray(aligned)
    factor = px(raw_cfg["width"]) / image.width
    size_ = (px(raw_cfg["width"]), round(image.height * factor))
    image = image.resize(size_, Image.LANCZOS)
    real_img = Image.fromarray(real).resize(size_, Image.NEAREST)
    box = (px(raw_cfg["origin"][0]), px(raw_cfg["origin"][1]))

    canvas = Image.new("RGB", (width, height), BACKGROUND)
    canvas.paste(image, box, real_img)
    mask = Image.new("L", (width, height), 0)
    mask.paste(255, box, real_img)

    raw_arr = np.asarray(canvas)
    out = raw_arr.copy()
    sx, sy, sw, sh = SCREENS[side]
    x0, y0, w, h = px(sx), px(sy), px(sw), px(sh)
    crisp = Image.open(ROOT / "work" / "panels" / slug / f"{side}.webp").convert("RGB")
    if crisp.size != (w, h):
        crisp = crisp.resize((w, h), Image.LANCZOS)
    crisp_arr = np.asarray(crisp)
    out[y0:y0 + h, x0:x0 + w] = crisp_arr
    mask.paste(255, (x0, y0, x0 + w, y0 + h))

    # Feather the 24px inner edge where the crisp panel meets the wider aligned_raw
    # so rounding differences between build.py's screen_rect and RAW never show.
    fw = 24
    if side == "left":
        alpha = np.linspace(1.0, 0.0, fw, dtype=np.float32)[None, :, None]
        out[y0:y0 + h, x0 + w - fw:x0 + w] = np.clip(
            crisp_arr[:, -fw:] * alpha + raw_arr[y0:y0 + h, x0 + w - fw:x0 + w] * (1.0 - alpha) + 0.5,
            0, 255,
        ).astype(np.uint8)
    else:
        alpha = np.linspace(0.0, 1.0, fw, dtype=np.float32)[None, :, None]
        out[y0:y0 + h, x0:x0 + fw] = np.clip(
            crisp_arr[:, :fw] * alpha + raw_arr[y0:y0 + h, x0:x0 + fw] * (1.0 - alpha) + 0.5,
            0, 255,
        ).astype(np.uint8)

    return out, np.asarray(mask) > 127


def smooth_warp_panel(panel, main, overlap_box, side, decay=2400):
    """Two-pass coarse-to-fine smooth optical-flow alignment of panel -> main in overlap_box,
    decaying smoothly to zero over `decay` px into the side panel."""
    height, width = panel.shape[:2]
    x0, y0, x1, y1 = overlap_box
    cur = panel.copy()

    bezel = x0 if side == "left" else x1
    xs = np.arange(width, dtype=np.float32)
    dist = np.maximum(0.0, bezel - xs) if side == "left" else np.maximum(0.0, xs - bezel)
    hx = np.clip(1.0 - dist / decay, 0.0, 1.0)
    hx = hx * hx * (3.0 - 2.0 * hx)
    active = np.flatnonzero(hx > 1e-4)
    c0, c1 = int(active[0]), int(active[-1]) + 1

    # Pass 1: broad features (limbs, horizons, rings); Pass 2: crisp high-gradient edges.
    passes = (
        (4, 35.0, 20.0, 48.0, 1.0),
        (2, 22.0, 12.0, 24.0, 2.0),
    )
    stats = []
    for scale, sigma, dx_lim, dy_lim, grad_pow in passes:
        hs, ws = (y1 - y0) // scale, (x1 - x0) // scale
        p_s = cv2.resize(cur[y0:y1, x0:x1], (ws, hs), interpolation=cv2.INTER_AREA)
        m_s = cv2.resize(main[y0:y1, x0:x1], (ws, hs), interpolation=cv2.INTER_AREA)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        pg = clahe.apply(cv2.cvtColor(p_s, cv2.COLOR_RGB2GRAY))
        mg = clahe.apply(cv2.cvtColor(m_s, cv2.COLOR_RGB2GRAY))

        dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        flow = dis.calc(mg, pg, None)

        gx = cv2.Sobel(mg, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(mg, cv2.CV_32F, 0, 1, ksize=3)
        grad = np.hypot(gx, gy)
        w_x = np.linspace(1.0, 0.2, ws, dtype=np.float32) if side == "left" else np.linspace(0.2, 1.0, ws, dtype=np.float32)
        weight = (np.clip(grad / 15.0, 0.0, 1.0) ** grad_pow) * w_x[None, :]
        w_sum = weight.sum(axis=1)
        dx_row = (flow[..., 0] * weight).sum(axis=1) / np.maximum(w_sum, 1e-4)
        dy_row = (flow[..., 1] * weight).sum(axis=1) / np.maximum(w_sum, 1e-4)
        conf = np.clip(w_sum / (ws * 0.03), 0.0, 1.0)

        w_smooth = cv2.GaussianBlur(conf[:, None], (1, 0), sigmaX=0, sigmaY=sigma)[:, 0]
        dx_s = cv2.GaussianBlur((dx_row * conf)[:, None], (1, 0), sigmaX=0, sigmaY=sigma)[:, 0] / np.maximum(w_smooth, 0.02)
        dy_s = cv2.GaussianBlur((dy_row * conf)[:, None], (1, 0), sigmaX=0, sigmaY=sigma)[:, 0] / np.maximum(w_smooth, 0.02)
        taper = np.clip(w_smooth / 0.08, 0.0, 1.0)
        dx_s *= taper
        dy_s *= taper

        dx_ov = np.clip(cv2.resize(dx_s[:, None], (1, y1 - y0), interpolation=cv2.INTER_LINEAR)[:, 0] * scale, -dx_lim, dx_lim)
        dy_ov = np.clip(cv2.resize(dy_s[:, None], (1, y1 - y0), interpolation=cv2.INTER_LINEAR)[:, 0] * scale, -dy_lim, dy_lim)

        dx_y = np.zeros(height, dtype=np.float32)
        dy_y = np.zeros(height, dtype=np.float32)
        dx_y[y0:y1] = dx_ov
        dy_y[y0:y1] = dy_ov
        fade_h = 400
        if y0 > 0:
            t = np.clip(1.0 - (y0 - np.arange(y0)) / fade_h, 0.0, 1.0)
            t = t * t * (3.0 - 2.0 * t)
            dx_y[:y0] = dx_y[y0] * t
            dy_y[:y0] = dy_y[y0] * t
        if y1 < height:
            t = np.clip(1.0 - (np.arange(y1, height) - y1 + 1) / fade_h, 0.0, 1.0)
            t = t * t * (3.0 - 2.0 * t)
            dx_y[y1:] = dx_y[y1 - 1] * t
            dy_y[y1:] = dy_y[y1 - 1] * t

        gx_sub = np.arange(c0, c1, dtype=np.float32)[None, :] + dx_y[:, None] * hx[None, c0:c1]
        gy_sub = np.arange(height, dtype=np.float32)[:, None] + dy_y[:, None] * hx[None, c0:c1]
        cur[:, c0:c1] = cv2.remap(cur, gx_sub, gy_sub, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        stats.append((float(np.abs(dx_ov).max()), float(np.abs(dy_ov).max())))
    return cur, stats


def tone_match_side(panel, main, overlap_box, side, reach=1800):
    """Smooth multiplicative gain + dark-gated bias matching panel's lighting to main at the overlap."""
    height, width = panel.shape[:2]
    x0, y0, x1, y1 = overlap_box
    band = 240
    bx0, bx1 = (x0, x0 + band) if side == "left" else (x1 - band, x1)
    m_med = np.median(main[y0:y1, bx0:bx1].astype(np.float32), axis=1)
    p_med = np.median(panel[y0:y1, bx0:bx1].astype(np.float32), axis=1)

    sigma = 80.0
    m_s = cv2.GaussianBlur(m_med[:, None, :], (1, 0), sigmaX=0, sigmaY=sigma)[:, 0, :]
    p_s = cv2.GaussianBlur(p_med[:, None, :], (1, 0), sigmaX=0, sigmaY=sigma)[:, 0, :]

    eps = 16.0
    gain_ov = np.clip((m_s + eps) / (p_s + eps), 0.35, 1.85)
    bias_ov = np.clip(m_s - gain_ov * p_s, -14.0, 14.0)

    gain_y = np.ones((height, 3), dtype=np.float32)
    bias_y = np.zeros((height, 3), dtype=np.float32)
    gain_y[y0:y1] = gain_ov
    bias_y[y0:y1] = bias_ov
    fade_h = 300
    if y0 > 0:
        t = np.clip(1.0 - (y0 - np.arange(y0)) / fade_h, 0.0, 1.0)
        t = (t * t * (3.0 - 2.0 * t))[:, None]
        gain_y[:y0] = 1.0 + (gain_y[y0] - 1.0) * t
        bias_y[:y0] = bias_y[y0] * t
    if y1 < height:
        t = np.clip(1.0 - (np.arange(y1, height) - y1 + 1) / fade_h, 0.0, 1.0)
        t = (t * t * (3.0 - 2.0 * t))[:, None]
        gain_y[y1:] = 1.0 + (gain_y[y1 - 1] - 1.0) * t
        bias_y[y1:] = bias_y[y1 - 1] * t

    bezel = x0 if side == "left" else x1
    xs = np.arange(width, dtype=np.float32)
    dist = np.maximum(0.0, bezel - xs) if side == "left" else np.maximum(0.0, xs - bezel)
    hx = np.clip(1.0 - dist / reach, 0.0, 1.0)
    hx = hx * hx * (3.0 - 2.0 * hx)

    g_eff = 1.0 + (gain_y[:, None, :] - 1.0) * hx[None, :, None]
    b_eff = bias_y[:, None, :] * hx[None, :, None]
    pf = panel.astype(np.float32)
    luma = pf[..., 0] * 0.2126 + pf[..., 1] * 0.7152 + pf[..., 2] * 0.0722
    dark_gate = np.clip((luma - 4.0) / 14.0, 0.0, 1.0)[..., None]
    b_eff = np.where(b_eff > 0, b_eff * dark_gate, b_eff)
    return np.clip(pf * g_eff + b_eff + 0.5, 0, 255).astype(np.uint8)


def dp_seam_x(main, panel, box, side):
    """Minimum-error vertical seam x(y) through `box`, avoiding bright point sources."""
    x0, y0, x1, y1 = box
    scale = 4
    hs, ws = (y1 - y0) // scale, (x1 - x0) // scale
    a = cv2.resize(main[y0:y1, x0:x1], (ws, hs), interpolation=cv2.INTER_AREA).astype(np.float32)
    b = cv2.resize(panel[y0:y1, x0:x1], (ws, hs), interpolation=cv2.INTER_AREA).astype(np.float32)
    err = np.linalg.norm(a - b, axis=2)
    lum = np.maximum(a.max(axis=2), b.max(axis=2))
    peak = np.maximum(0.0, lum - cv2.GaussianBlur(lum, (0, 0), 6.0))
    xs = np.arange(ws, dtype=np.float32)
    dist_bezel = xs / ws if side == "left" else (ws - 1 - xs) / ws
    cost = err + 0.6 * peak + 6.0 * (dist_bezel[None, :] ** 2)

    dp = np.empty_like(cost)
    back = np.zeros((hs, ws), dtype=np.int32)
    dp[0] = cost[0]
    for r in range(1, hs):
        prev = dp[r - 1]
        left_p = np.concatenate(([1e12], prev[:-1]))
        right_p = np.concatenate((prev[1:], [1e12]))
        stacked = np.stack([left_p, prev, right_p], axis=0)
        idx = np.argmin(stacked, axis=0)
        dp[r] = cost[r] + stacked[idx, np.arange(ws)]
        back[r] = idx - 1
    col = int(np.argmin(dp[-1]))
    path = np.empty(hs, dtype=np.float32)
    for r in range(hs - 1, -1, -1):
        path[r] = col
        col += int(back[r, col])
    path = cv2.GaussianBlur(path[:, None], (1, 0), sigmaX=0, sigmaY=4.0)[:, 0]
    return cv2.resize(path[:, None], (1, y1 - y0), interpolation=cv2.INTER_LINEAR)[:, 0] * scale + x0


def painted(slug):
    """Everything painted for the scene, placed without blending (used by --canvas)."""
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
        "main": main_panel_path(slug),
        "left": ROOT / "work" / "panels" / slug / "left.webp",
        "right": ROOT / "work" / "panels" / slug / "right.webp",
    }
    for name, path in crisp.items():
        x, y, w, h = SCREENS[name]
        image = Image.open(path).convert("RGB")
        if image.size != (px(w), px(h)):
            image = image.resize((px(w), px(h)), Image.LANCZOS)
        pano.paste(image, (px(x), px(y)))
        mask.paste(255, (px(x), px(y), px(x + w), px(y + h)))
    return np.array(pano), np.asarray(mask) > 127


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
    pano, covered = painted(slug)
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
    """The generator's painting of the gap canvas, aligned, tone-matched and enlarged onto the panorama; None without one."""
    raw = build.RAW / f"{slug}-gaps.png"
    if not raw.exists():
        return None
    canvas = build.load(build.CANVAS / f"{slug}-gaps-canvas.png")
    out = build.align(build.load(raw), canvas, GAP_ALIGN)
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
    height, width = px(LAYOUT[1]), px(LAYOUT[0])
    mx, my, mw, mh = (px(v) for v in SCREENS["main"])
    main_img = Image.open(main_panel_path(slug)).convert("RGB")
    if main_img.size != (mw, mh):
        main_img = main_img.resize((mw, mh), Image.LANCZOS)
    main_arr = np.asarray(main_img)
    main_full = np.zeros((height, width, 3), dtype=np.uint8)
    main_full[my:my + mh, mx:mx + mw] = main_arr

    left_layer, left_mask = side_layer(slug, "left", (height, width))
    right_layer, right_mask = side_layer(slug, "right", (height, width))

    ov_left = (mx, my, px(RAW["left"]["origin"][0] + RAW["left"]["width"]), my + mh)
    ov_right = (px(RAW["right"]["origin"][0]), my, mx + mw, my + mh)

    left_w, st_l = smooth_warp_panel(left_layer, main_full, ov_left, "left")
    left_t = tone_match_side(left_w, main_full, ov_left, "left")
    right_w, st_r = smooth_warp_panel(right_layer, main_full, ov_right, "right")
    right_t = tone_match_side(right_w, main_full, ov_right, "right")
    print(f"  warp left:  pass1=({st_l[0][0]:.1f},{st_l[0][1]:.1f}) pass2=({st_l[1][0]:.1f},{st_l[1][1]:.1f}) px")
    print(f"  warp right: pass1=({st_r[0][0]:.1f},{st_r[0][1]:.1f}) pass2=({st_r[1][0]:.1f},{st_r[1][1]:.1f}) px")

    mid_x = mx + mw // 2
    sides_base = np.empty((height, width, 3), dtype=np.uint8)
    sides_base[:, :mid_x] = left_t[:, :mid_x]
    sides_base[:, mid_x:] = right_t[:, mid_x:]
    covered = np.zeros((height, width), dtype=bool)
    covered[:, :mid_x] = left_mask[:, :mid_x]
    covered[:, mid_x:] = right_mask[:, mid_x:]
    covered[my:my + mh, mx:mx + mw] = True

    stitched = sides_base.copy()
    stitched[my:my + mh, mx:mx + mw] = main_arr

    seam_l = dp_seam_x(main_full, left_t, (mx, my, mx + 600, my + mh), "left")
    seam_r = dp_seam_x(main_full, right_t, (mx + mw - 600, my, mx + mw, my + mh), "right")

    for side, panel_img, seam_x, cx in (
        ("left", left_t, seam_l, mx),
        ("right", right_t, seam_r, mx + mw),
    ):
        wx0, wx1 = cx - 900, cx + 900
        a = main_full[my:my + mh, wx0:wx1].astype(np.float32)
        b = panel_img[my:my + mh, wx0:wx1].astype(np.float32)
        if side == "left":
            a[:, :900] = a[:, 900:901]
        else:
            a[:, 900:] = a[:, 899:900]
        cols = np.arange(wx1 - wx0, dtype=np.float32)[None, :]
        sx_rel = (seam_x - wx0)[:, None]
        mask = (cols >= sx_rel).astype(np.float32) if side == "left" else (cols < sx_rel).astype(np.float32)
        blended = np.clip(multiband(a, b, mask, levels=7) + 0.5, 0, 255).astype(np.uint8)
        stitched[my:my + mh, wx0 + 200:wx1 - 200] = blended[:, 200:-200]

    monitors = np.zeros((height, width), dtype=bool)
    for sx, sy, sw, sh in SCREENS.values():
        monitors[px(sy):px(sy + sh), px(sx):px(sx + sw)] = True

    layer = generated_surroundings(slug, (height, width))
    if layer is not None:
        x0 = px(GAP_X)
        ramp = np.clip((np.arange(width, dtype=np.float32) - x0) / px(50), 0, 1)
        ramp = (ramp * ramp * (3 - 2 * ramp))[None, :, None]
        surroundings = np.clip(sides_base.astype(np.float32) * (1 - ramp) + layer.astype(np.float32) * ramp + 0.5,
                               0, 255).astype(np.uint8)
        print("  surroundings: generated")
    else:
        surroundings = np.where(covered[..., None], sides_base, edge_fill(sides_base, covered))
        print("  surroundings: panels, gaps faded from the edges (no work/raw/<scene>-gaps.png)")

    reference = surroundings.copy()
    reference[monitors] = stitched[monitors]
    outer = surroundings.astype(np.float32) + membrane(reference, monitors)
    del reference, surroundings, layer
    inner = outer.copy()
    inner[monitors] = stitched[monitors]
    joined = np.clip(multiband(inner, outer, monitors.astype(np.float32), levels=6) + 0.5, 0, 255).astype(np.uint8)
    del inner, outer

    image = Image.fromarray(joined)
    out = ROOT / "backgrounds" / f"{slug}.webp"
    image.save(out, "WEBP", quality=QUALITY, method=6)
    print(f"  {out.relative_to(ROOT)}  {image.width}x{image.height}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    args = sys.argv[1:]
    canvas_only = "--canvas" in args
    slugs = [a for a in args if a != "--canvas"] or sorted(
        p.parent.name for p in (ROOT / "work" / "panels").glob("[0-9][0-9]-*/main.webp"))
    for slug in slugs:
        if canvas_only:
            print(slug)
            gap_canvas(slug)
        else:
            assemble(slug)
