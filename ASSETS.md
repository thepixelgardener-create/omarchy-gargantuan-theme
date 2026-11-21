# Assets

## Wallpapers

The nine wallpapers are AI-generated, painted by the image tool built into OpenAI's Codex from the prompts in GENERATION.md. The theme's namesake comes first; the other eight climb the Kardashev scale.

| File | Idea |
|---|---|
| `01-gargantuan.webp` | A supermassive black hole seen almost edge-on: the far side of its accretion disk lensed over and under the shadow, the approaching side brighter |
| `02-fusion.webp` | Inside a fusion reactor: a broad band of hydrogen plasma floating through the tiled vacuum vessel, which curves away on both sides like an endless tunnel |
| `03-core.webp` | A rocky planet with a wedge cut out, showing crust, mantle, molten outer core and a white-hot inner core |
| `04-ocean.webp` | Thalassa, a planet covered by one ocean, seen from orbit at the terminator with spiral storms and a sun-glint path |
| `05-elevator.webp` | Tether, a space elevator rising from an ocean world through the atmosphere at sunrise, a climber on the cable |
| `06-giant.webp` | A ringed gas giant seen from inside its asteroid belt, two small moons beside it |
| `07-lifter.webp` | Star Lifter, a ring of machines pulling a twisting column of plasma out of a red-orange star into a collector |
| `08-dyson.webp` | A Dyson sphere two-thirds built around a yellow-white star, light escaping through its gaps, a construction swarm in orbit |
| `09-gate.webp` | A ring-shaped gate whose opening folds space into a tunnel toward a distant spiral galaxy, a small ship approaching |

All nine are shipped as a single set of seamless **9840 × 3840** WebP panoramas at quality 88, together 9.7 MB.

## How the panoramas are assembled

The generator returns at most 1672 × 941 and cannot paint a 9840 × 3840 panorama in one pass. Each scene was therefore painted outward from its centre panel across a 4920 × 1920 logical canvas at 2× density, as GENERATION.md describes: left and right canvases each carried a 480-logical-px overlap strip of the centre image, and a final gap pass painted the strips above and below the centre and right regions.

`tools/build.py` aligns, colour-matches, crops and upscales the centre (`3840 × 2160`), left (`2160 × 3840`) and right (`3840 × 2160`) panels into `work/panels/<scene>/`:

1. **Coarse alignment.** The generator repaints the whole canvas, its copy of the strip included, and that copy can drift by a few pixels or change scale slightly. SIFT features in the strip are matched against the original strip and a similarity transform (shift, scale, rotation) fitted with RANSAC moves the painted panel back into register. Where the strip is too dark for features, the shift is found by phase correlation.
2. **Coarse brightness.** The brightness of the original and painted strips is compared row by row near the join; where a single uniform gain brings them closer, it is applied.

`tools/panorama.py` then stitches all pieces into one seamless `backgrounds/<scene>.webp`:

1. **Panel layers.** Each side's upscaled panel is placed onto its wider aligned raw layer (which includes the 960-pixel overlap with the centre panel), feathering the 24-pixel inner edge so sub-pixel crop rounding never shows.
2. **Fine overlap registration.** Inside each 960-pixel overlap, a two-pass coarse-to-fine smooth optical-flow warp (DIS optical flow weighted by local edge gradient) aligns horizons, planetary limbs, rings and disks to the centre panel, decaying smoothly to zero across the side panel.
3. **Smooth lighting match.** Each side panel's exposure and colour are matched to the centre panel along the overlap with a smooth per-row multiplicative gain and a small dark-gated residual bias (so deep space stays dark), fading smoothly across the side panel.
4. **Seam and multi-band join.** A dynamic-programming minimum-error seam (penalising bright isolated peaks so stars and suns are never split) is found through each overlap corridor, and the centre and side panels are joined with a 7-level Burt–Adelson multi-band blend.
5. **Surroundings.** The final gap painting (`work/raw/<scene>-gaps.png`) is aligned and quantile-mapped onto the right-hand 16:9 of the canvas, evened out toward the stitched panels with a harmonic tone membrane (Laplace's equation on a 16-pixel grid), and joined with a 6-level multi-band blend.

Four left panels were rejected at review because the generator painted the main subject a second time (Core, Giant, Star Lifter and Gate) and were painted again with stricter prompts. The rejected images are not shipped.

## Upscaling

The generator returned the centre and right images at 1672 × 941 and the left images at 1024 × 1536. The three main panels were enlarged 4× with Real-ESRGAN (`realesrgan-x4plus`, realesrgan-ncnn-vulkan 0.2.5.0), resized to target with Lanczos, and blended 65 % Real-ESRGAN with 35 % plain Lanczos enlargement: it keeps Real-ESRGAN's sharper edges without smoothed, plastic surfaces. The upscaled detail is synthesized, not recovered. Outside the main panels, the outer edges and gap painting are plain Lanczos enlargements.

## Cropping and overlays

Each panorama is 9840 × 3840 (2.56:1), with the primary subject near the middle so standard 16:9, 16:10, 3:2, ultrawide and multi-monitor displays all frame cleanly:

- **Gargantuan** keeps the shadow, photon ring and lensed arcs in the middle with the disk running out to both sides.
- **Fusion** runs its plasma band straight across the middle through the curving reactor tunnel.
- **Core** puts the cut-open planet near the centre with deep space, embers and a distant moon to the sides.
- **Thalassa** fills the lower half with the endless ocean and spiral storms under dark space.
- **Tether** keeps the space elevator and sunrise horizon across the middle with clouds curving away on both sides.
- **Giant** frames the ringed gas giant and asteroid field across the middle with the distant star to the left.
- **Star Lifter** keeps the plasma column and collector in the middle above the curved solar surface.
- **Dyson** keeps the partially enclosed star in the middle with the orbital swarm rings extending to both sides.
- **Gate** frames the ring gate and folded galaxy tunnel near the centre in dark space.

Lock screen and launcher text sits in the middle of the screen and lands on the subject in most of these. The overlay checks in DESIGN.md use black and white bounds rather than samples from the artwork, so they hold for every wallpaper at the modeled opacity.

## License

The repository's MIT license covers the palette, the notes, the scripts and the images. The 36 source images are AI-generated.
