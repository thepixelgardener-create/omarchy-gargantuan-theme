"""Validate continuous exports and make a contact sheet plus unscaled detail samples."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'output/coherent-theme/backgrounds'
REVIEW = ROOT / 'work/quality-audit/coherent'
REVIEW.mkdir(parents=True, exist_ok=True)
SLUGS = ['01-gargantuan', '02-fusion', '03-core', '04-ocean', '05-elevator',
         '06-giant', '07-lifter', '08-dyson', '09-gate']
sheet = Image.new('RGB', (1500, 690), '#0a0d16')
draw = ImageDraw.Draw(sheet)
inventory = []
for i, slug in enumerate(SLUGS):
    for prefix, size in [('', (3840, 2160)), ('span-', (9840, 3840))]:
        path = SOURCE / f'{prefix}{slug}.webp'
        with Image.open(path) as im:
            im.load()
            if im.size != size:
                raise ValueError(f'{path.name}: {im.size}, expected {size}')
            inventory.append({'file': path.name, 'size': im.size,
                              'bytes': path.stat().st_size,
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            if prefix:
                x, y = i % 3 * 500, i // 3 * 230
                draw.text((x + 8, y + 6), slug, fill='white')
                sheet.paste(im.resize((492, 192), Image.Resampling.LANCZOS), (x + 4, y + 25))
                # Three 512px squares at their actual exported pixel size.
                details = Image.new('RGB', (1536, 540), '#0a0d16')
                labels = ImageDraw.Draw(details)
                for j, (cx, cy) in enumerate([(0.25, 0.52), (0.50, 0.42), (0.75, 0.52)]):
                    left, top = round(im.width * cx) - 256, round(im.height * cy) - 256
                    details.paste(im.crop((left, top, left + 512, top + 512)), (j * 512, 28))
                    labels.text((j * 512 + 8, 7), f'{slug} | x={cx:.0%} | 100% pixels', fill='white')
                details.save(REVIEW / f'{slug}-detail.png')
sheet.save(REVIEW / 'panoramas.png')
(REVIEW / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
print(f'Validated {len(inventory)} exports; review: {REVIEW}')
