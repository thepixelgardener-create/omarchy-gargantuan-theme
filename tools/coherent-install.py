"""Install verified continuous exports locally, backing up every replaced file."""
from pathlib import Path
from PIL import Image
import datetime, hashlib, shutil, json

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'output/coherent-theme/backgrounds'
SLUGS = ['01-gargantuan','02-fusion','03-core','04-ocean','05-elevator','06-giant','07-lifter','08-dyson','09-gate']
files = [(s + '.webp', (3840,2160)) for s in SLUGS] + [('span-' + s + '.webp', (9840,3840)) for s in SLUGS]
for name, size in files:
    with Image.open(SOURCE / name) as im:
        im.load()
        assert im.size == size, (name, im.size)
backup = ROOT / 'work/coherent-install-backup' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
targets = {'project':ROOT / 'backgrounds', 'installed':Path.home()/'.config/omarchy/themes/gargantuan/backgrounds'}
state = Path.home()/'.local/state/omarchy/current'
if (state/'theme.name').read_text().strip() == 'gargantuan':
    targets['active'] = state/'theme/backgrounds'
for label, target in targets.items():
    (backup/label).mkdir(parents=True, exist_ok=True)
    for name, _ in files:
        if (target/name).exists(): shutil.copy2(target/name, backup/label/name)
        temp = target/('.'+name+'.tmp')
        shutil.copyfile(SOURCE/name,temp)
        temp.replace(target/name)
        assert hashlib.sha256((target/name).read_bytes()).digest() == hashlib.sha256((SOURCE/name).read_bytes()).digest()
for slug in SLUGS:
    (backup/'previews').mkdir(exist_ok=True)
    old_preview = ROOT/'previews'/(slug+'.webp')
    if old_preview.exists(): shutil.copy2(old_preview, backup/'previews'/old_preview.name)
    pano=Image.open(SOURCE/('span-'+slug+'.webp'))
    preview=Image.new('RGB',(1270,520),(10,13,22))
    for x,y,w,h in [(0,0,1080,1920),(1080,480,1920,1080),(3000,550,1920,1080)]:
        tile=pano.crop((x*2,y*2,(x+w)*2,(y+h)*2)).resize((round(w/4)-6,round(h/4)-6),Image.Resampling.LANCZOS)
        preview.paste(tile,(23+round(x/4),23+round(y/4)))
    preview.save(ROOT/'previews'/(slug+'.webp'),quality=92,method=6)
print(json.dumps({'installed':list(targets), 'files':len(files), 'backup':str(backup)},indent=2))
