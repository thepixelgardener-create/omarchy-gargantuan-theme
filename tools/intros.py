#!/usr/bin/env python3
"""Generate procedural Omarchy background intro animations from the 4K stills.

    uv run --no-project --with numpy --with pillow --with opencv-python-headless \
        python -I tools/intros.py [NN-slug ...]

Each intro is a 7-second, 30 fps H.264 clip at 2560 x 1440 written to
backgrounds/intros/<slug>.mp4. Motion uses dual-layer flow-map advection and
physically coupled light modulation that rise smoothly out of the still over
the first 1.2 s and settle back to the exact still over the final 1.8 s, so
the first and last frames match the wallpaper with zero handover jump.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BG_DIR = ROOT / "backgrounds"
OUT_DIR = BG_DIR / "intros"

W, H = 2560, 1440
FPS = 30
DURATION = 7.0
FRAMES = int(round(FPS * DURATION))  # 210 frames (0..209)


def smootherstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def envelope(t):
    """0 at t=0 and t=1, smooth rise 0..1.2s, smooth settle 5.2..7.0s."""
    sec = t * DURATION
    rise = smootherstep(sec / 1.2)
    fall = smootherstep((DURATION - sec) / 1.8)
    return float(rise * fall)


def load_base(slug):
    path = BG_DIR / f"{slug}.webp"
    im = Image.open(path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    return np.asarray(im, dtype=np.float32)


def make_grid():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    return x, y


def flow_advect(img, x_grid, y_grid, vx, vy, phase, amp):
    """Dual-layer phase-blended flow advection returning exact `img` when amp == 0."""
    if amp <= 1e-5:
        return img.copy()
    p0 = phase % 1.0
    p1 = (phase + 0.5) % 1.0
    w0 = 1.0 - abs(2.0 * p0 - 1.0)
    w1 = 1.0 - w0

    d0 = (p0 - 0.5) * amp
    d1 = (p1 - 0.5) * amp

    m0x = x_grid - vx * d0
    m0y = y_grid - vy * d0
    m1x = x_grid - vx * d1
    m1y = y_grid - vy * d1

    l0 = cv2.remap(img, m0x, m0y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    l1 = cv2.remap(img, m1x, m1y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    return w0 * l0 + w1 * l1


def encode_frames(slug, frame_iter):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{slug}.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for frame in frame_iter:
        proc.stdin.write(np.clip(frame + 0.5, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed for {slug} (exit {rc})")
    print(f"  {out_path.relative_to(ROOT)}  {W}x{H}  {DURATION:.1f}s  {out_path.stat().st_size / 1e6:.2f} MB", flush=True)


def render_gargantuan():
    """01-gargantuan: relativistic orbital flow along the accretion disk & lensed arcs, subtle Doppler shimmer."""
    img = load_base("01-gargantuan")
    xg, yg = make_grid()
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722

    # Shadow center & disk geometry (measured at 2560x1440)
    cx, cy, disk_y = 1352.0, 735.0, 749.0
    dx, dy = xg - cx, yg - cy
    r = np.hypot(dx, dy) + 1e-4

    # Luminous gas mask, strictly excluding the pitch-black shadow interior
    gas_mask = np.clip((lum - 18.0) / 55.0, 0.0, 1.0)
    gas_mask *= np.clip((r - 235.0) / 35.0, 0.0, 1.0)
    gas_mask = cv2.GaussianBlur(gas_mask, (0, 0), 10.0)

    # Blend horizontal disk streaming near y=disk_y with tangential orbital flow around the lensed arcs
    disk_w = np.exp(-0.5 * ((yg - disk_y) / 95.0) ** 2)
    # Tangential clockwise flow around (cx, cy): (-dy/r, dx/r)
    tx, ty = -dy / r, dx / r
    # Horizontal rightward flow along front disk plane
    radial_falloff = np.clip(1.25 - np.abs(dx) / 1450.0, 0.35, 1.15)
    vx = (disk_w * 26.0 * radial_falloff + (1.0 - disk_w) * tx * 20.0) * gas_mask
    vy = ((1.0 - disk_w) * ty * 20.0) * gas_mask

    # Approaching left wing & photon ring shimmer mask
    bright_core = np.clip((lum - 85.0) / 110.0, 0.0, 1.0)
    bright_core = cv2.GaussianBlur(bright_core, (0, 0), 14.0)
    left_bias = np.clip(1.15 - (xg - 600.0) / 1200.0, 0.25, 1.0)
    shimmer_mask = (bright_core * left_bias)[..., None]
    warm_tint = np.array([1.08, 0.98, 0.85], dtype=np.float32)

    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        env = envelope(t)
        frame = flow_advect(img, xg, yg, vx, vy, phase=t * 1.4, amp=env)
        pulse = (0.045 * np.sin(2 * np.pi * t * 1.5) + 0.025 * np.sin(2 * np.pi * t * 3.0 + 0.7)) * env
        frame = frame * (1.0 + pulse * shimmer_mask * warm_tint)
        yield frame


def render_fusion():
    """02-fusion: hydrogen plasma drifting through the tokamak with reactive wall bounce light & LED breath."""
    img = load_base("02-fusion")
    xg, yg = make_grid()
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722

    # Plasma band strictly localized around y=736, high luminance
    band_y = np.exp(-0.5 * ((yg - 736.0) / 170.0) ** 2)
    plasma_mask = np.clip((lum - 55.0) / 85.0, 0.0, 1.0) * band_y
    plasma_mask = cv2.GaussianBlur(plasma_mask, (0, 0), 12.0)

    # Smooth horizontal flow + gentle magnetic filament wave
    vx = 28.0 * plasma_mask
    vy = (4.5 * np.sin(xg * 0.009) * np.exp(-0.5 * ((yg - 736.0) / 110.0) ** 2)) * plasma_mask

    # Reactive indirect bounce light on the dark curved tunnel walls above & below
    wall_zone = np.exp(-0.5 * ((yg - 736.0) / 480.0) ** 2) * (1.0 - plasma_mask * 0.6)
    wall_zone *= np.clip((lum - 6.0) / 45.0, 0.0, 1.0)
    wall_zone = cv2.GaussianBlur(wall_zone, (0, 0), 25.0)[..., None]

    # Tiny amber diagnostic indicator lights outside the plasma band
    amber = np.clip((img[..., 0] - img[..., 2] - 70.0) / 80.0, 0.0, 1.0) * np.clip((lum - 60.0) / 80.0, 0.0, 1.0)
    amber *= (1.0 - band_y)
    amber = cv2.GaussianBlur(amber, (0, 0), 6.0)[..., None]

    rose_tint = np.array([1.05, 0.92, 1.08], dtype=np.float32)

    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        env = envelope(t)
        frame = flow_advect(img, xg, yg, vx, vy, phase=t * 1.6, amp=env)
        p_wave = (0.055 * np.sin(2 * np.pi * t * 2.0) + 0.025 * np.sin(2 * np.pi * t * 3.5 + 1.1)) * env
        led_wave = 0.14 * np.sin(2 * np.pi * t * 1.5 + 0.4) * env
        frame = frame * (1.0 + p_wave * (plasma_mask[..., None] * 0.6 + wall_zone) * rose_tint)
        frame = frame * (1.0 + led_wave * amber)
        yield frame


def render_engines():
    """03-engines: parallel fusion thruster beams streaming down-left at 157.05 deg + nozzle shimmer."""
    img = load_base("03-engines")
    xg, yg = make_grid()
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    blue_exc = img[..., 2] - 0.5 * (img[..., 0] + img[..., 1])

    # Measured exact beam direction: 157.05 deg (down-left)
    theta = np.radians(157.05)
    ux, uy = float(np.cos(theta)), float(np.sin(theta))  # (-0.9208, +0.3899)
    # Beam coordinate along exhaust direction (increases moving outward down-left)
    u_coord = xg * ux + yg * uy

    # Strict geometric region for exhaust beams (below/left of planet upper-right sunlit rim)
    # Keep planet upper-right rim and distant star completely frozen
    beam_region = smootherstep((2060.0 - xg) / 260.0) * smootherstep((yg - 620.0) / 180.0)
    # Exclude dark space & dark rocky planet body using blue-white glow
    beam_mask = np.clip((lum - 14.0) / 36.0, 0.0, 1.0) * np.clip((blue_exc - 3.0) / 11.0, 0.0, 1.0) * beam_region
    beam_mask = cv2.GaussianBlur(beam_mask, (0, 0), 7.0)

    # Bright nozzle ignition cores on the planet's lower-left edge
    nozzle_mask = np.clip((lum - 75.0) / 80.0, 0.0, 1.0) * np.clip((blue_exc - 8.0) / 18.0, 0.0, 1.0) * beam_region
    nozzle_mask = cv2.GaussianBlur(nozzle_mask, (0, 0), 6.0)[..., None]

    vx = 42.0 * ux * beam_mask
    vy = 42.0 * uy * beam_mask
    cyan_tint = np.array([0.82, 0.96, 1.18], dtype=np.float32)

    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        env = envelope(t)
        frame = flow_advect(img, xg, yg, vx, vy, phase=t * 2.2, amp=env)
        # Traveling thrust pulses streaming outward down-left along u_coord
        travel = (0.16 * np.sin(u_coord * 0.015 - 2 * np.pi * t * 3.0)
                  + 0.09 * np.sin(u_coord * 0.033 - 2 * np.pi * t * 5.0 + 1.3)) * env
        nozzle_flicker = (0.18 * np.sin(2 * np.pi * t * 3.5) + 0.09 * np.sin(2 * np.pi * t * 6.5 + 0.9)) * env
        frame = frame * (1.0 + (travel * beam_mask)[..., None] * cyan_tint + nozzle_flicker * nozzle_mask * cyan_tint)
        yield frame


def render_lifter():
    """07-lifter: twisting solar plasma column streaming upward into the dark collector ring + solar shimmer."""
    img = load_base("07-lifter")
    xg, yg = make_grid()
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    warm = np.clip((img[..., 0] - img[..., 2]) / 90.0, 0.0, 1.0)

    # Plasma column zone (between collector throat y=180 and solar surface y=1020)
    col_x_env = np.exp(-0.5 * ((xg - 1265.0) / 280.0) ** 2)
    col_y_env = smootherstep((yg - 165.0) / 55.0) * smootherstep((1060.0 - yg) / 90.0)
    col_mask = np.clip((lum - 32.0) / 65.0, 0.0, 1.0) * warm * col_x_env * col_y_env
    col_mask = cv2.GaussianBlur(col_mask, (0, 0), 10.0)

    # Star photosphere below the curved limb (keep machine ring dark specks crisp by limiting displacement to 6px)
    star_top = 990.0 + ((xg - 1280.0) / 1000.0) ** 2 * 220.0
    star_mask = smootherstep((yg - star_top) / 80.0) * np.clip((lum - 45.0) / 80.0, 0.0, 1.0) * warm
    star_mask = cv2.GaussianBlur(star_mask, (0, 0), 14.0)

    # Upward helical flow in plasma column + gentle horizontal convective drift on star surface
    vx = (7.0 * np.sin(yg * 0.014) * col_mask) + (7.0 * star_mask)
    vy = (-32.0 * col_mask) + (-3.0 * np.sin(xg * 0.012) * star_mask)

    # Shadowed underside of the collector ring catching rising warm glow
    collector_zone = np.exp(-0.5 * ((xg - 1300.0) / 420.0) ** 2) * smootherstep((340.0 - yg) / 90.0)
    collector_mask = collector_zone * np.clip((lum - 12.0) / 55.0, 0.0, 1.0)
    collector_mask = cv2.GaussianBlur(collector_mask, (0, 0), 16.0)[..., None]

    gold_tint = np.array([1.10, 0.96, 0.78], dtype=np.float32)

    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        env = envelope(t)
        frame = flow_advect(img, xg, yg, vx, vy, phase=t * 1.8, amp=env)
        surge = (0.06 * np.sin(-yg * 0.012 + 2 * np.pi * t * 2.5)
                 + 0.03 * np.sin(-yg * 0.025 + 2 * np.pi * t * 4.0 + 0.6)) * env
        coll_pulse = 0.08 * np.sin(2 * np.pi * t * 2.5 - 0.5) * env
        frame = frame * (1.0 + (surge * (col_mask + 0.35 * star_mask))[..., None] * gold_tint
                         + coll_pulse * collector_mask * gold_tint)
        yield frame


def render_gate():
    """09-gate: hypnotic swirl inside the folded-space aperture + cyan rim pulse + ship engine glint."""
    img = load_base("09-gate")
    xg, yg = make_grid()
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    cyan = img[..., 2] + 0.6 * img[..., 1] - 1.2 * img[..., 0]

    # Exact fitted inner aperture ellipse from cyan rim measurement
    cx, cy = 1613.5, 728.8
    ang = np.radians(57.0)
    ca, sa = float(np.cos(ang)), float(np.sin(ang))
    dx, dy = xg - cx, yg - cy
    # Rotate into ellipse principal axes (semi-axes: a=381, b=692 -> shrink inside metal ring)
    u = dx * ca + dy * sa
    v = -dx * sa + dy * ca
    # Normalized elliptical radius (1.0 at cyan inner rim)
    er = np.hypot(u / 355.0, v / 645.0)

    # Strictly inside the folded-space opening (zero motion on machined metal ring!)
    aperture_mask = smootherstep((0.96 - er) / 0.14)
    aperture_mask = cv2.GaussianBlur(aperture_mask, (0, 0), 8.0)

    # Elliptical tangential swirl + tiny inward pull toward galaxy tunnel center (1820, 770)
    gx, gy = 1820.0, 770.0
    rx, ry = xg - gx, yg - gy
    rr = np.hypot(rx, ry) + 1e-4
    # Tangential + gentle inward spiral, zero right at core so the galaxy nucleus doesn't blur
    core_guard = smootherstep(rr / 90.0)
    speed = 18.0 * core_guard * aperture_mask
    vx = (-ry / rr * 0.92 - rx / rr * 0.35) * speed
    vy = (rx / rr * 0.92 - ry / rr * 0.35) * speed

    # Cyan inner rim glow mask (thin ring around er in [0.92, 1.12])
    rim_band = np.exp(-0.5 * ((er - 1.02) / 0.08) ** 2)
    rim_mask = rim_band * np.clip((cyan - 50.0) / 80.0, 0.0, 1.0)
    rim_mask = cv2.GaussianBlur(rim_mask, (0, 0), 8.0)[..., None]

    # Tiny approaching ship engine glint at (566, 924)
    ship_r = np.hypot(xg - 566.0, yg - 924.0)
    ship_mask = np.exp(-0.5 * (ship_r / 28.0) ** 2) * np.clip((lum - 30.0) / 80.0, 0.0, 1.0)
    ship_mask = ship_mask[..., None]

    cyan_tint = np.array([0.82, 1.02, 1.14], dtype=np.float32)
    amber_tint = np.array([1.18, 0.98, 0.72], dtype=np.float32)

    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        env = envelope(t)
        frame = flow_advect(img, xg, yg, vx, vy, phase=t * 1.3, amp=env)
        rim_pulse = 0.06 * np.sin(2 * np.pi * t * 1.5) * env
        ship_pulse = (0.14 * np.sin(2 * np.pi * t * 4.0) + 0.07 * np.sin(2 * np.pi * t * 7.0 + 0.5)) * env
        frame = frame * (1.0 + rim_pulse * rim_mask * cyan_tint + ship_pulse * ship_mask * amber_tint)
        yield frame


SCENES = {
    "01-gargantuan": render_gargantuan,
    "02-fusion": render_fusion,
    "03-engines": render_engines,
    "07-lifter": render_lifter,
    "09-gate": render_gate,
}


if __name__ == "__main__":
    slugs = sys.argv[1:] or list(SCENES)
    for slug in slugs:
        if slug not in SCENES:
            raise SystemExit(f"unknown intro scene: {slug} (choices: {', '.join(SCENES)})")
        print(f"rendering {slug}...", flush=True)
        encode_frames(slug, SCENES[slug]())
