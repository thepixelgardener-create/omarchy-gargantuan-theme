#!/usr/bin/env python3
"""Upscale single-pass source images into shipped 4K (3840 x 2160) WebP wallpapers.

    uv run --no-project --with numpy --with pillow python -I tools/build.py [NN-slug ...]

Reads source images from work/new_gen/ (falling back to work/raw/) and writes
3840 x 2160 WebP files to backgrounds/NN-slug.webp. Upscaling blends 4x
Real-ESRGAN (realesrgan-x4plus) with a plain Lanczos enlargement (65/35) to
keep sharp edges without smoothed, plastic surfaces.
"""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
SOURCES = (WORK / "new_gen", WORK / "raw")
ESRGAN = WORK / "bin/realesrgan/realesrgan-ncnn-vulkan"
UPSCALED = WORK / "upscaled"
SIZE = (3840, 2160)
ESRGAN_SHARE = 0.65
QUALITY = 92


def find_source(slug):
    for folder in SOURCES:
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = folder / f"{slug}{ext}"
            if p.exists():
                return p
    raise FileNotFoundError(f"no source image found for {slug}")


def esrgan(img, key):
    """4x Real-ESRGAN of an RGB array, cached under work/upscaled/ by name and content."""
    UPSCALED.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(np.ascontiguousarray(img).tobytes()).hexdigest()[:10]
    out = UPSCALED / f"{key}-{digest}.png"
    if not out.exists():
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.png"
            Image.fromarray(img).save(src)
            subprocess.run(
                [str(ESRGAN), "-i", str(src), "-o", str(out), "-n", "realesrgan-x4plus", "-t", "64"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
    return np.asarray(Image.open(out).convert("RGB"))


def upscale(src_path, slug):
    orig = Image.open(src_path).convert("RGB")
    big = Image.fromarray(esrgan(np.asarray(orig), slug)).resize(SIZE, Image.LANCZOS)
    plain = orig.resize(SIZE, Image.LANCZOS)
    mixed = ESRGAN_SHARE * np.asarray(big, np.float32) + (1 - ESRGAN_SHARE) * np.asarray(plain, np.float32)
    return np.clip(mixed + 0.5, 0, 255).astype(np.uint8)


def build(slug):
    src = find_source(slug)
    img = upscale(src, slug)
    out = ROOT / "backgrounds" / f"{slug}.webp"
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(out, "WEBP", quality=QUALITY, method=6)
    print(f"  {out.relative_to(ROOT)}  {SIZE[0]}x{SIZE[1]}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    slugs = sys.argv[1:] or sorted({
        p.stem for folder in SOURCES if folder.exists()
        for p in folder.glob("[0-9][0-9]-*")
        if not p.stem.endswith(("-left", "-right", "-gaps"))
    })
    for slug in slugs:
        build(slug)
