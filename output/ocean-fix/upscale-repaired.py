"""Rebuild only the seamless panorama, without the old stitched-panel pipeline.
Run: uv run --with pillow --with numpy --with opencv-python python output/ocean-fix/upscale-repaired.py
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('theme_build', ROOT / 'tools/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
source = ROOT / 'output/ocean-fix/span-04-ocean-repaired.png'
result = build.upscale(build.load(source), (9840, 3840), '04-ocean-repaired-panorama')
build.save_webp(result, ROOT / 'output/ocean-fix/span-04-ocean-repaired-9840.webp')
