"""Export a continuous generated panorama and its centred single-screen crop.
Run with uv --with pillow --with numpy.
Never assembles or reintroduces old side panels.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'output/coherent-theme/backgrounds'
DEST.mkdir(parents=True, exist_ok=True)
UPSCALED = ROOT / 'work/upscaled'
ESRGAN = ROOT / 'work/bin/realesrgan/realesrgan-ncnn-vulkan'
MODELS = ROOT / 'work/bin/realesrgan/models-general'

def check_enhancement(source, enhanced):
    """Catch silent GPU failures before dark/empty tiles reach the final blend."""
    if enhanced.size != (source.width * 4, source.height * 4):
        raise ValueError(f'Invalid enhanced dimensions: {enhanced.size}')
    original = np.asarray(source, dtype=np.float32)
    reduced = np.asarray(enhanced.resize(source.size, Image.Resampling.BOX), dtype=np.float32)
    error = float(np.abs(original - reduced).mean())
    if error > 20:
        raise ValueError(f'Enhancement changed image luminance/content: mean error {error:.2f}')
    for y in range(0, source.height, 32):
        for x in range(0, source.width, 32):
            before = original[y:y+32, x:x+32].mean()
            after = reduced[y:y+32, x:x+32].mean()
            if before > 8 and after < before * 0.4:
                raise ValueError(f'Missing/dark upscale tile near source pixel {x},{y}')
    print(f'CHECK mean source difference {error:.2f}/255; no missing tiles', flush=True)

def enhance(source, raw, slug):
    UPSCALED.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(np.asarray(source).tobytes()).hexdigest()[:10]
    cached = UPSCALED / f'{slug}-continuous-general-v3-{digest}.png'
    if not cached.exists():
        temp = cached.with_suffix('.partial.png')
        log = UPSCALED / f'{slug}-upscale.log'
        with log.open('w') as output:
            subprocess.run([str(ESRGAN), '-i', str(raw), '-o', str(temp),
                            '-m', str(MODELS), '-n', 'realesrgan-general-x4v3',
                            '-t', '64', '-j', '1:1:1'],
                           stdout=output, stderr=output, check=True)
        with Image.open(temp) as im:
            im.load()
            check_enhancement(source, im)
        temp.replace(cached)
    enhanced = Image.open(cached).convert('RGB')
    check_enhancement(source, enhanced)
    return enhanced

def valid_image(path, size):
    try:
        with Image.open(path) as im:
            im.load()
            return im.size == size
    except (OSError, ValueError):
        return False

def save_atomic(im, path):
    temp = path.with_suffix('.tmp')
    im.save(temp, 'WEBP', quality=95, method=6)
    temp.replace(path)

for slug in sys.argv[1:]:
    if slug not in {'01-gargantuan', '02-fusion', '03-core', '04-ocean',
                    '05-elevator', '06-giant', '07-lifter', '08-dyson', '09-gate'}:
        raise ValueError(f'Unknown scene: {slug}')
    target = DEST / ('span-' + slug + '.webp')
    single = DEST / (slug + '.webp')
    print('START', slug, flush=True)
    raw = ROOT / 'output/coherent-theme/raw' / (slug + '.png')
    if slug == '04-ocean':
        approved = ROOT / 'output/ocean-fix/span-04-ocean-repaired-9840.webp'
        if not valid_image(approved, (9840, 3840)):
            raise ValueError('Approved ocean panorama missing or invalid')
        temp = target.with_suffix('.tmp')
        shutil.copyfile(approved, temp)
        temp.replace(target)
        with Image.open(target) as pano:
            save_atomic(ImageOps.fit(pano, (3840, 2160), method=Image.Resampling.LANCZOS), single)
        print('RETAINED approved ocean panorama', flush=True)
        continue
    source = Image.open(raw).convert('RGB')
    enhanced = enhance(source, raw, slug)
    if valid_image(target, (9840, 3840)) and valid_image(single, (3840, 2160)):
        print('EXISTS', slug, flush=True)
        continue
    size = (9840, 3840)
    big = np.asarray(enhanced.resize(size, Image.Resampling.LANCZOS), dtype=np.float32)
    plain = np.asarray(source.resize(size, Image.Resampling.LANCZOS), dtype=np.float32)
    pano = Image.fromarray(np.clip(big * 0.65 + plain * 0.35 + 0.5, 0, 255).astype(np.uint8))
    save_atomic(pano, target)
    save_atomic(ImageOps.fit(pano, (3840, 2160), method=Image.Resampling.LANCZOS), single)
    print('DONE', slug, flush=True)
