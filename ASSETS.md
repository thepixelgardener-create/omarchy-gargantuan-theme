# Assets

## Wallpapers

The nine wallpapers are single-pass AI-generated 16:9 images, with no multi-panel stitching or seams. The theme's namesake comes first; the other eight climb the Kardashev scale.

| File | Idea |
|---|---|
| `01-gargantuan.webp` | A supermassive black hole seen almost edge-on: the far side of its accretion disk lensed over and under the shadow, the approaching side brighter |
| `02-fusion.webp` | Inside a fusion reactor: a broad band of hydrogen plasma floating through the tiled vacuum vessel, which curves away on both sides like an endless tunnel |
| `03-engines.webp` | Planetary Engines, a barren world of dark rock and ice pushed out of its orbit by a band of fusion thrusters firing parallel blue-white exhaust into space, lit only along one limb by a distant star |
| `04-orbital.webp` | Orbital, a colossal razor-thin ringworld habitat tilted across deep space, dark armour in shadow with a sunlit inner strip of oceans and clouds and faint amber city lights on the night curve |
| `05-elevator.webp` | Tether, a space elevator rising from an ocean world through the atmosphere at sunrise, a climber on the cable |
| `06-shkadov.webp` | Stellar Engine, a colossal dark parabolic Shkadov Thruster mirror hovering beside a solitary star, reflecting a razor-thin band of gold-white starlight along its concave rim |
| `07-lifter.webp` | Star Lifter, a ring of machines pulling a twisting column of plasma out of a red-orange star into a collector |
| `08-dyson.webp` | A Dyson sphere two-thirds built around a yellow-white star, light escaping through its gaps, a construction swarm in orbit |
| `09-gate.webp` | A ring-shaped gate whose opening folds space into a tunnel toward a distant spiral galaxy, a small ship approaching |
| `intros/01-gargantuan.mp4` | Gargantuan's intro: hot gas flows along the accretion disk and lensed arcs with subtle Doppler shimmer |
| `intros/02-fusion.mp4` | Fusion's intro: confined hydrogen plasma ripples through the tokamak while the dark chamber walls and indicator lights catch its glow |
| `intros/03-engines.mp4` | Planetary Engines' intro: parallel blue-white fusion exhaust plumes stream outward down-left with subtle nozzle shimmer |
| `intros/07-lifter.mp4` | Star Lifter's intro: the twisting plasma vortex streams upward from the boiling star into the dark collector ring |
| `intros/09-gate.mp4` | Gate's intro: the folded-space aperture swirls quietly inside the rigid ring while the inner cyan rim and approaching ship's engine pulse |

All nine stills are shipped as a single set of **3840 × 2160** WebP files at quality 92–94, together 3.2 MB.

## Animated intros

The five clips under `backgrounds/intros/` are 7-second, 30 fps H.264 High (`yuv420p`, `bt709`, `+faststart`) animations at **2560 × 1440** — matching the built-in Omarchy themes' intros — generated procedurally from the 4K stills by `tools/intros.py` rather than by a video model. Each clip uses dual-layer phase-blended flow-map advection and physically coupled lighting modulation masked strictly to the luminous gas, plasma, exhaust or folded-space aperture, keeping rigid structures and deep space completely still. Motion ramps smoothly out of the still over the first 1.2 s and settles back over the final 1.8 s so the first and last frames match the still wallpaper with no handover jump.

## Provenance and upscaling

- `01-gargantuan`, `02-fusion`, `05-elevator`, `07-lifter` and `08-dyson` were generated as single-pass 16:9 (`1376 × 768`) images with Gemini image generation guided by the original compositions and prompts recorded in `GENERATION.md`; `04-orbital` and `06-shkadov` were generated as original single-pass 16:9 (`1376 × 768`) compositions with Gemini image generation.
- `03-engines` and `09-gate` are original single-pass 16:9 (`1672 × 941`) images painted by OpenAI Codex's image tool from the prompts in `GENERATION.md`.
- All nine were upscaled 4× with Real-ESRGAN (`realesrgan-x4plus`, realesrgan-ncnn-vulkan 0.2.5.0), resized to **3840 × 2160** with Lanczos, and blended 65 % Real-ESRGAN with 35 % plain Lanczos enlargement via `tools/build.py`: it keeps Real-ESRGAN's sharper edges without smoothed, plastic surfaces. The upscaled detail is synthesized, not recovered.

## Cropping and overlays

On a 16:9 screen every wallpaper is shown whole. Other shapes crop around the centre:

- **Gargantuan** keeps the shadow, photon ring and lensed arcs in the middle; ultrawide trims the outer vertical space while keeping the full disk.
- **Fusion** runs its plasma band straight across the middle through the curving reactor tunnel.
- **Planetary Engines** keeps the shadowed planet right of centre with its exhaust columns trailing into the empty dark toward the lower left.
- **Orbital** tilts the colossal ring diagonally across deep space, keeping both the sunlit inner ribbon and night-side curve framed cleanly.
- **Tether** keeps the hair-fine tether, climber and sunrise horizon across the middle.
- **Stellar Engine** centres the solitary star and colossal shadowed mirror arc in vast empty dark space.
- **Star Lifter** keeps the plasma column and collector in the middle above the curved solar surface.
- **Dyson** keeps the partially enclosed sphere and orbital rings framed in dark space.
- **Gate** frames the ring gate, folded galaxy tunnel and tiny approaching ship in dark space.

Lock screen and launcher text sits in the middle of the screen and lands on the subject in most of these. The overlay checks in DESIGN.md use black and white bounds rather than samples from the artwork, so they hold for every wallpaper at the modeled opacity.

## License

The repository's MIT license covers the palette, the notes, the scripts and the images. The wallpapers are AI-generated.
