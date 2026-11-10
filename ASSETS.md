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

All nine are 3840 × 2160 WebP files at quality 92, like the WebP wallpapers of the built-in Omarchy themes, together 5.7 MB.

## Panoramas

Every scene also comes as `span-<name>.webp`: 9840 × 3840, one image of the whole three-monitor layout in README.md at twice its logical size, WebP at quality 88, together 9.4 MB. Each holds three kinds of painting:

- **The wallpaper** on the main screen's rectangle, pixel for pixel the 4K wallpaper.
- **Two cuts of the panels** on the left and right screens' rectangles, 2160 × 3840 and 3840 × 2160: the parts of the scene beyond the wallpaper's left and right edges.
- **The surroundings**, everything no monitor covers. Left of the main screen that is the rest of the left panel as the generator painted it. Around the main and right screens it is one further painting, made in a last pass, which also fills the strips above and below those screens that neither the wallpaper nor the panels reach, about a quarter of the panorama.

On the layout the panoramas were made for, at Station's default framing, every monitor shows its 4K image; the surroundings appear when the framing moves or the monitors are arranged differently.

The generator returns at most 1672 × 941 and cannot paint the whole panorama, so the panels were painted outward from the wallpapers, as GENERATION.md describes: each canvas carried a strip from the edge of the wallpaper, and the tool painted the rest of the canvas around it. `tools/build.py` then made the cuts for the monitors:

1. **Alignment.** The generator repaints the whole canvas, its copy of the strip included, and that copy can drift by a few pixels or change scale slightly. SIFT features in the strip are matched against the original strip and a similarity transform (shift, scale, rotation) fitted with RANSAC moves the painted panel back into register. Where the strip is too dark for features, the shift is found by phase correlation of the strip as a whole. The largest corrections were a 30 px shift (Giant's right panel) and a 1.7 % rescale (Tether's left panel); most were under 5 px.
2. **Brightness.** The brightness of the original and the painted strip is compared row by row in the 16 columns next to the seam, the part the eye compares across the bezel. If one gain, the same for all three channels so hues and black space are kept, brings them clearly closer, it is applied; it was for five of the eighteen panels, by 0.85 to 1.12.
3. **Cut.** Each cut is exactly the area its screen covers in the layout, so the content at its edge is what continues beyond the wallpaper's edge.

The cuts never contain the strip itself: the main screen shows the wallpaper, so whatever the generator did to its copy is cut away.

`tools/panorama.py` puts each panorama together:

1. **Placing.** Each panel, aligned and brightness-matched as above, goes at its canvas's position in the layout, without the few rows and columns the alignment moved it away from (the warp repeats the panel's edge there, which shows as streaks). The wallpaper and the two cuts go on the monitors' rectangles.
2. **The last painting.** `--canvas` writes the right-hand 16:9 of that panorama, which holds every unpainted strip, at the generator's size with the strips flat grey. Codex painted the grey away with the GAPS prompt in GENERATION.md, one attempt per scene. The generator repaints the whole canvas and lifts its darks, so the result is aligned on the main screen's part, as for the panels, and each colour channel's distribution is mapped back onto the canvas's. It then replaces everything around the main and right screens, not only the strips: one consistent painting leaves no joins between panel and strip. It eases in over 100 pixels from the left panel.
3. **Tone.** The surroundings still differ a little in tone from the monitors' images. A smooth correction is added to them: next to a monitor it is the difference between the blurred colours on both sides of its edge, elsewhere the smoothest field between those values (Laplace's equation on a 16-pixel grid).
4. **Joining.** The monitors' images are set into the surroundings by multi-band blending (Burt and Adelson, six levels): fine detail switches at the monitor's edge, broad tone and haze cross it over about a hundred pixels. Along the edges that face the surroundings this changes the monitors' own pixels slightly; between 97.8 % (Star Lifter) and 100 % of them stay within one level of the 4K images.

The joins between two monitors' images, the vertical lines at x 2160 and 6000, are left as they are: the bezels lie there.

Four left panels were rejected at review because the generator painted the main subject a second time (Core, Giant, Star Lifter and Gate) and were painted again with stricter prompts. The rejected images are not shipped.

## Upscaling

The generator returned the wallpapers at 1672 × 941. The shown part of each panel was 1338 × 753 (right) and 709 × 1260 (left) of the generator's pixels. The wallpapers and the monitors' cuts were enlarged 4× with Real-ESRGAN (`realesrgan-x4plus`, realesrgan-ncnn-vulkan 0.2.5.0), resized to the target with Lanczos, and blended 65 % Real-ESRGAN with 35 % of a plain Lanczos enlargement of the original, the same method as Farbenlehre's wallpapers: it keeps Real-ESRGAN's sharper edges without its smoothed, plastic surfaces. The upscaled detail is synthesized, not recovered: fine texture at 4K is the upscaler's interpretation of the original. Outside the monitors, the left panel's outer part (about 3×) and the last painting (about 4×) are plain Lanczos enlargements and softer; they are the edge of the frame.

## Cropping and overlays

On a 16:9 screen every wallpaper is shown whole. Other shapes crop it:

- **Gargantuan** keeps the shadow and photon ring in the middle; 21:9 trims the lensed arcs above and below, 16:10 and 3:2 trim the outer ends of the disk.
- **Fusion** runs its plasma band straight across the middle; every crop keeps it, and 21:9 trims the ports above and below.
- **Core** puts the planet right of centre with dark space on the left; 3:2 cuts into the planet's lit limb on the right.
- **Thalassa** fills the lower half with the ocean; 21:9 trims the sky, 3:2 trims the planet's curve at both sides.
- **Tether** keeps the tether left of centre and the horizon across the middle; every crop keeps both.
- **Giant** puts the planet top right and asteroids along the bottom; 21:9 trims the top of the planet.
- **Star Lifter** keeps the plasma column in the middle and the star along the bottom; 21:9 trims the collector at the top.
- **Dyson** keeps the sphere in the middle; every crop keeps all of it.
- **Gate** puts the gate right of centre; 3:2 trims the gate's outer rim on the right.

Lock screen and launcher text sits in the middle of the screen and lands on the subject in most of these. The overlay checks in DESIGN.md use black and white bounds rather than samples from the artwork, so they hold for every wallpaper and panorama at the modeled opacity.

## Previews

`previews/<name>.webp` show each scene across three screens at a quarter of their logical size, placed as in the layout table in README.md, with dark bezels between them: what Station shows of a panorama on that layout. They are drawn from the wallpapers and the monitors' cuts by `tools/build.py --previews`.

## License

The repository's MIT license covers the palette, the notes, the scripts and the images. The 36 images are AI-generated.
