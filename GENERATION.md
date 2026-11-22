# Wallpaper generation

All 36 images, nine wallpapers, their eighteen span panels and nine paintings that complete the panoramas, were painted by the image generation tool built into OpenAI's Codex (the `gpt-6.1-sol` agent in Codex CLI 0.167), from the prompts below. The tool returns fixed sizes: 1672 × 941 for 16:9 and 1024 × 1536 for 2:3 portrait. Codex saved every result unaltered; nothing was painted over or retouched afterwards. ASSETS.md describes how the panels were then aligned and how everything was upscaled.

## How the panels were made

A span shows one scene on three monitors: a portrait screen on the left, the main 16:9 screen in the middle and a 16:9 screen on the right. The generator cannot paint that panorama in one image, so each scene was built outward from its wallpaper:

1. The wallpaper was generated from the style paragraph and the scene's own paragraph.
2. `tools/span-canvas.py` cut the outer quarter of the wallpaper, scaled it to the panel's scale and placed it at the edge of a flat grey canvas: a 2:3 portrait canvas for the left panel, a 16:9 canvas for the right.
3. Codex gave each canvas to the image tool as the image to edit, with the LEFT or RIGHT prompt, and the tool painted the grey away.

The strip of the wallpaper on each canvas is what makes the scene continue across the bezel: the generator paints outward from it at its scale, in its light.

Portrait panels had one recurring failure: the generator wanted a picture of its own and painted the main subject a second time, a second cut-open planet, gas giant, Dyson sphere, plasma column or gate. Revision 2 of the LEFT prompt and the left notes marked (rev. 2) below say outright that the subject is not in the panel; with them every redone panel passed on its first attempt.

## Style (opens every wallpaper prompt)

A 16:9 widescreen desktop wallpaper for Gargantuan, a dark desktop theme about colossal structures in space. Cinematic, photorealistic science-fiction concept art with the physical plausibility and overwhelming sense of scale of a high-end space film. Deep blue-black space (#0a0d16) fills most of the frame; the light is concentrated in the subject and falls off into darkness, leaving quiet, uncluttered dark areas where desktop windows and text can sit. Precise, physically motivated lighting, rich but restrained colour, subtle film grain. The scene continues naturally past the left and right edges of the frame: no vignette and no framing devices at the edges. No text, letters, numbers, logos, insignia, symbols, watermarks, signatures, borders, user interface or people.

## LEFT prompt

Revision 1:

> Extend this wallpaper to the left. The input image is a tall portrait canvas. The narrow vertical strip on its right side is the left edge of an existing 16:9 wallpaper, described below. Everything flat mid-gray is empty canvas: paint it so the scene continues seamlessly to the left of the strip and above and below it, as if the same camera simply had a wider and taller field of view. Keep the strip's content exactly where it is, at the same scale, perspective, light direction, colour, grain and level of detail. Continue every element that crosses the strip's edges along its natural path. This panel is shown on its own portrait monitor beside the main screen, so give it a calm composition of its own over its full height: {LEFT NOTE}. Keep large areas dark. No gray left over, no seams, no borders, no text, no people.
> The wallpaper: {WALLPAPER PARAGRAPH}

Revision 2 replaces the sentence that begins "This panel is shown" with:

> This panel is shown on a portrait monitor to the left of the main screen. It is the far left edge of the same scene, not a new picture: the main subject lies to the right of the strip and must not appear again here, so paint no second planet, sphere, ring, gate or structure, and do not re-centre the composition. What it shows: {LEFT NOTE}.

## RIGHT prompt

> Extend this wallpaper to the right. The input image is a wide 16:9 canvas. The narrow vertical strip on its left side is the right edge of an existing 16:9 wallpaper, described below. Everything flat mid-gray is empty canvas: paint it so the scene continues seamlessly to the right of the strip and above and below it, as if the same camera simply had a wider field of view. Keep the strip's content exactly where it is, at the same scale, perspective, light direction, colour, grain and level of detail. Continue every element that crosses the strip's edges along its natural path. This panel is shown on its own monitor beside the main screen, so give it a calm composition of its own: {RIGHT NOTE}. Keep large areas dark. No gray left over, no seams, no borders, no text, no people.
> The wallpaper: {WALLPAPER PARAGRAPH}

Every prompt asked for a 16:9 landscape or a 2:3 portrait in words; the size itself cannot be prompted.

## GAPS prompt

The wallpaper and the two panels do not cover the whole three-monitor layout: strips above and below the main and right screens stay empty. `tools/panorama.py --canvas` wrote, for each scene, the right-hand 16:9 of its panorama with those strips flat grey, and Codex gave it to the image tool with this prompt. All nine passed on the first attempt. ASSETS.md describes how the results were set into the panoramas.

> Fill in the missing parts of this panoramic wallpaper. The input image is a 16:9 crop of a wide space scene that spans several monitors. Everything flat mid-gray is empty canvas: a few strips along the top and bottom edges. Paint only those gray strips, so the scene continues seamlessly into them, as if the same camera had captured the whole frame at once. Continue every element that reaches a gray strip along its natural path, at the same scale, perspective, light direction, colour, grain and level of detail: the curve of a planet's limb or a ring, a tether, the plasma, clouds, ocean, fire, rock, dust and the star field. Keep everything already painted exactly where it is and as it is: do not move, rescale, recolour or redraw it, and do not re-centre the composition. Add nothing new in the strips: no second planet, moon, sphere, ring, gate or structure, and no new bright light. Where nothing reaches a strip, it is quiet dark space with sparse faint stars, like the dark areas next to it. No gray left over, no seams, no borders, no vignette, no text, no people.
> The scene: {WALLPAPER PARAGRAPH}

## The scenes

Attempts count every image generated for that file, including those rejected by Codex or by the alignment review. They were checked against Codex's own folder of generated images: each kept image is byte-identical to one of them.

### 01 Gargantuan

**Wallpaper** (1 attempt): Gargantuan. A supermassive black hole seen almost edge-on, rendered with physically accurate gravitational lensing: a perfectly black shadow at the centre ringed by a thin, brilliant photon ring; the accretion disk of glowing gas wraps around it, and its far side is bent by gravity into a luminous arc that rises over the top of the shadow and loops beneath it. Relativistic Doppler beaming makes the approaching side of the disk blazing white-gold, faintly blue at its brightest, and the receding side dimmer amber and deep red. The flat disk extends far out to both sides past the edges of the frame. The background starfield is warped and stretched into arcs around the black hole. Immense, silent, overwhelming. Mostly black space; the disk is the only light.

**Left note** (rev. 1, 1 attempt): the accretion disk's outer edge continuing as a thin flat band with the colour and brightness it has at the strip's edge, fading into faint glowing dust; lensed, stretched stars relaxing into an ordinary starfield; deep black above and below

**Right note** (1 attempt): the disk's other outer edge continuing as a thin flat band with the colour and brightness it has at the strip's edge, fading into faint glowing dust; lensed stars relaxing into an ordinary starfield; deep black above and below

### 02 Fusion

This is the second version. The first showed a bright violet ribbon that read as lightning, filled the frame and looked unlike the other eight; it was redone from the inside of the reactor, composed as one broad scene for three screens. Its prompts are in this file's history.

**Wallpaper** (1 attempt): A star in a bottle, seen from inside. The inner chamber of a colossal fusion reactor, as if photographed by a camera inside a real tokamak: its doughnut-shaped vacuum vessel is lined with thousands of dark graphite and tungsten armour tiles, bolted panels and round diagnostic ports, and its inner walls curve away to the left and to the right, so the chamber reads as an endless arched tunnel bending out of sight on both sides. Through the middle of the tunnel floats the plasma: a broad, softly glowing band of hydrogen plasma at a hundred million degrees, suspended in vacuum without touching anything, pale rose and lavender at its translucent edges and white-hot at its dense core, with fine filaments twisted along the magnetic field lines. The band runs horizontally across the whole width of the frame, a little below the middle, and continues past both edges, following the curve of the vessel. Its glow is the only light: it catches the edges of the tiles in pale rose and violet and falls away into deep shadow on the upper and lower walls, where a few tiny amber indicator lights glow. The plasma is luminous gas, never lightning, sparks or electric arcs. Wide, calm and enormous, mostly dark steel and shadow.

**Left note** (rev. 2, 1 attempt): the plasma band continues from the strip, curving away along the vessel into the depth of the tunnel and growing fainter, and there is no second band; the tiled inner wall continues to the left and arches up overhead and down below like the inside of a vast tube, its tiles and ports lit at their edges by the plasma near the middle and falling into deep shadow toward the top and bottom of the panel

**Right note** (1 attempt): the plasma band continues from the strip, following the curve of the vessel and receding into the depth of the tunnel to a soft glowing vanishing point; the tiled inner wall continues around it above and below, fading into darkness

### 03 Planetary Engines (replaced Core)

**Wallpaper** (OpenAI Codex image tool, 4 attempts: one with Gemini image generation had exhaust leaving in two opposite directions and read as a ring; three with Codex, the second kept): A 16:9 widescreen desktop wallpaper for a dark desktop theme about colossal structures in space. Cinematic, photorealistic science-fiction concept art with the physical plausibility and overwhelming sense of scale of a high-end space film. Hanging in vast, silent deep blue-black space (#0a0d16), a single barren world of dark rock and grey ice is being pushed out of its orbit. The planet sits right of centre and fills roughly a third of the frame height; it is almost entirely in shadow, with only a thin, cold silver crescent of light from a small distant star along its upper-right limb. On the planet's hemisphere facing the lower left, a band of a few dozen planetary engines, each a mountain-sized fusion thruster that is still only a pinprick against the planet, fires in unison. ALL exhaust points in ONE single direction: hair-fine, perfectly straight, parallel columns of pale blue-white plasma stream away from the planet only toward the lower left, extending thousands of kilometres back into space and fading softly into the dark. There is no exhaust on the far side and nothing passes behind or through the planet; the columns must never read as a ring. The exhaust is thin and restrained, never fiery explosions; its faint glow catches the nearby terrain in a delicate blue rim. About 70% of the frame is empty, quiet deep blue-black space with only sparse faint pinpoint stars. Restrained colour, precise physically motivated lighting, subtle film grain. No Earth, no oceans, no continents, no clouds, no cities, no moons. No text, letters, numbers, logos, symbols, watermarks, borders, user interface or people.

*(Previously slot 03 held Core, a rocky planet with a wedge cut out to show its molten interior; replaced on 2026-11-22.)*

### 04 Orbital (replaced Thalassa)

**Wallpaper** (Gemini image generation, 16:9): Seen from deep space in vast, silent blue-black darkness (`#0a0d16`), a single incomprehensibly massive ring-shaped artificial world (thousands of kilometres across, like a Niven ringworld or Culture Orbital) tilts gracefully across the frame at a sweeping three-quarter perspective. Most of the colossal band is plunged in dark shadow, its razor-thin exterior armour catching only a faint silver edge of starlight. Along the far curving inner surface, direct light from an unseen distant star illuminates an impossibly delicate narrow strip of deep sapphire ocean, wispy white cloud bands, and tiny continent shadows — all dwarfed by the sheer width and emptiness of the ring's immense black outer hull and the vast void inside it. Along the dark night-side inner curve approaching the foreground, only microscopic, hair-fine pinpoint constellations of warm amber lights hint at civilisations living inside the band, making the scale feel staggering.

*(Previously slot 04 held Thalassa, an ocean world; replaced on 2026-11-22.)*

### 05 Tether

**Wallpaper** (1 attempt): A road to orbit. A space elevator seen from the edge of space, a hundred kilometres above an ocean world at sunrise. A single, impossibly thin tether rises straight up from a sea platform far below, through the cloud deck and the glowing blue layers of the atmosphere, and on up out of the frame into black space toward a station tens of thousands of kilometres away. A climber the size of a building ascends the cable, its windows catching the first sunlight. The curvature of the planet spans the frame, the sunrise burning a thin gold line along the horizon. The tether is a hair-fine line of light, a little left of centre, and its fineness is what makes the height feel colossal.

**Left note** (rev. 1, 2 attempts): the curved horizon and atmosphere continuing, the dawn glow fading into blue night over the ocean; above, deep black space full of faint stars, and very high up a small bright orbital station glinting

**Right note** (3 attempts): the curved horizon continuing toward the sunrise, the gold line brightening, cloud patterns over the ocean far below; above, black space

Both panels kept painting a second tether. For the final attempts Codex added its own instruction to paint only sky, atmosphere, ocean and clouds; that added wording was not recorded.

### 06 Stellar Engine (replaced Giant)

**Wallpaper** (Gemini image generation, 16:9): Hanging in vast, silent deep blue-black space (`#0a0d16`), a solitary warm yellow-white star glows quietly near the lower-left center, and suspended at a colossal orbital distance beside and curving around its upper-right hemisphere is a single incomprehensibly vast, paper-thin parabolic megastructure mirror — a smooth, dark metallic spherical-cap arc spanning millions of kilometres across space. Most of the gargantuan mirror's convex outer back is plunged in pitch-black shadow against the void, while its vast concave inner face catches a restrained, searing band of reflected gold-white starlight along its razor-thin curved rim, creating a dramatic, silent geometric composition of light and shadow. Almost 80% of the 16:9 frame is empty, quiet deep blue-black space (`#0a0d16`) with only sparse faint pinpoint stars.

*(Previously slot 06 held Giant, a ringed gas giant in an asteroid belt; replaced on 2026-11-22.)*

### 07 Star Lifter

**Wallpaper** (1 attempt): Harvesting a star. A colossal megastructure mines a red-orange star: a ring of enormous machines orbits close above the star's boiling surface and bends its magnetic field to pull a vast, twisting column of plasma up out of the photosphere. The stream of stellar matter, gold and white-hot at its base and cooling to deep orange and red as it rises, spirals along invisible field lines into a collector structure far above. The star fills the lower part of the frame with a granulated surface, sunspots and arching prominences; the machines are tiny dark silhouettes against it, revealing the inconceivable scale.

**Left note** (rev. 2, 4 attempts: three with rev. 1 each added a second plasma column and collector): the plasma column and its collector are NOT in this panel: they lie to the right, beyond the strip, so paint no second column, stream, funnel or collector here. The star's curved limb continues down and to the left with only small, low arching prominences close to its surface; the orbiting machine ring continues along the limb as a thin chain of small dark silhouettes and glints; the upper two thirds are dark space with sparse faint stars

**Right note** (1 attempt): the star's limb continuing, with a second, fainter plasma stream rising from another part of the surface toward its own collector; the machine ring continuing around the curve

### 08 Dyson

**Wallpaper** (1 attempt): A star being enclosed. A Dyson sphere under construction around a yellow-white star, seen from far enough away that the whole sphere is visible: a shell built from millions of hexagonal collector panels on a lattice framework, about two-thirds complete. Through the unfinished gaps the star blazes out in sharp beams of white and gold light that cut across space, while the finished sections glow a dull orange with the heat they absorb. Swarms of tiny construction craft and loose panels orbit around the sphere in thin glinting rings. Mostly dark: the finished shell swallows most of the light.

**Left note** (rev. 1, 3 attempts; the first two painted another sphere, and for the third Codex added that the sphere stays off the panel): a stream of new panels and construction craft flowing in a long arc toward the sphere; a beam of light from a gap in the shell continuing out into space

**Right note** (1 attempt): the orbiting swarm rings continuing around the sphere; far away, a slim orbital factory building panels, tiny in the distance; deep space

### 09 Gate

**Wallpaper** (1 attempt): A gate between galaxies. A colossal ring-shaped gate hangs in interstellar space, seen at a slight angle: a dark, precisely machined torus hundreds of kilometres across, with faint blue light along its inner rim. Inside the ring space itself is folded: instead of the stars behind it, the opening shows a tunnel of bent light leading to somewhere else, the bright spiral of a distant galaxy at its far end, while the stars around the ring's edge are smeared into concentric arcs by gravitational lensing. A tiny ship with a single glowing engine approaches the gate, giving it a monstrous sense of scale. Cool cyan, electric blue and white against blue-black space, with one faint warm accent from the ship's engine. No glyphs, symbols or chevrons on the ring.

**Left note** (rev. 2, 4 attempts: three with rev. 1 each painted a second gate): the gate is NOT in this panel: it lies entirely to the right, beyond the strip, so paint no ring, portal, tunnel or galaxy here. Continue the strip's dark starfield and any faint lensed star streaks, relaxing into an ordinary starfield; a faint line of tiny distant beacon lights running toward the right, marking the approach lane; deep space

**Right note** (1 attempt): the ring's outer edge wherever it crosses the strip, the lensed arcs relaxing into an ordinary starfield, and a faint dark nebula far away
