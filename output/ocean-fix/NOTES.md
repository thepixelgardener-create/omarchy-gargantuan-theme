# Water-planet panorama repair

Built-in image editing tool, using backgrounds/span-04-ocean.webp as the edit target.

Prompt: repair the two vertical stitched-panel joins around 22% and 61% of the width; make the planetary horizon one smooth arc, continue cloud patterns and atmospheric lighting, and remove the right-panel brightness jump and duplicate sunlight reflection. Preserve the approximately 2.5625:1 framing, dark sky, upper-left crescent moon, blue all-water planet, spiral storms and night-side lightning. No land, text or monitor outlines.

Result: span-04-ocean-repaired.png, 2007 × 783. Visually inspected: no visible vertical panel breaks; horizon and lighting are continuous. The image editor also repainted fine cloud details. This is the edited source, not a restored-detail 9840 × 3840 export. Shipped theme files were preserved while the question about the intended defect is pending.

## Installed upscale

The approved repaired source was subsequently upscaled with the existing theme pipeline: Real-ESRGAN x4plus, 64-pixel tiles, 65% enhanced + 35% Lanczos blend, resized to 9840 × 3840 and encoded as WebP quality 92. Result: `span-04-ocean-repaired-9840.webp`. This preserves the seamless composition and synthesizes additional detail. Both the local Gargantuan theme source and active theme copy were replaced; old installed copies are backed up under `work/ocean-install-backup/`. The published GitHub theme was not changed.
