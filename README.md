<img src="assets/icon.svg" width="64" height="64" alt="">

# Gargantuan

A dark theme for [Omarchy](https://omarchy.org) about the largest things a civilisation could build or meet. Deep-space surfaces, starlight text and an amber accent taken from the accretion disk of a black hole, with nine 4K wallpapers of colossal structures in space.

![Gargantuan: a supermassive black hole with a lensed accretion disk](backgrounds/01-gargantuan.webp)

## Install

From the Omarchy menu: press **Super + Space**, then **Install → Style → Theme**, and paste the repository URL when it asks:

```
https://github.com/thepixelgardener-create/omarchy-gargantuan-theme
```

Or straight from a terminal:

```sh
omarchy theme install https://github.com/thepixelgardener-create/omarchy-gargantuan-theme
```

Omarchy installs and activates the theme, generating application colors from `colors.toml`. Cycle wallpapers with **Super + Ctrl + Space**.

## Wallpapers

Nine scenes, the theme's namesake first and then a climb up the Kardashev scale, from a star in a bottle to a gate between galaxies. Click any image for the full **3840 × 2160** 4K original.

| Gargantuan | Fusion |
| --- | --- |
| [![Gargantuan: a supermassive black hole with a lensed accretion disk](backgrounds/01-gargantuan.webp)](backgrounds/01-gargantuan.webp) | [![Fusion: a band of glowing plasma floating through the tiled tunnel of a fusion reactor](backgrounds/02-fusion.webp)](backgrounds/02-fusion.webp) |
| A supermassive black hole. Gravity bends the far side of its disk over and under the shadow, and the side rushing toward you burns brighter. | A star in a bottle: a band of hydrogen plasma floating through the inside of a fusion reactor, whose tiled walls curve away like an endless tunnel. |

| Planetary Engines | Orbital |
| --- | --- |
| [![Planetary Engines: a dark planet pushed by a band of fusion thrusters](backgrounds/03-engines.webp)](backgrounds/03-engines.webp) | [![Orbital: a colossal ringworld tilted across deep space](backgrounds/04-orbital.webp)](backgrounds/04-orbital.webp) |
| Moving a world: a band of mountain-sized fusion engines pushing a barren planet out of its orbit. | A world built as a ring: a colossal orbital habitat thousands of kilometres across, dark armour in shadow with a sunlit ribbon of oceans and clouds inside. |

| Tether | Stellar Engine |
| --- | --- |
| [![Tether: a space elevator rising from an ocean world at sunrise](backgrounds/05-elevator.webp)](backgrounds/05-elevator.webp) | [![Stellar Engine: a colossal parabolic Shkadov Thruster mirror hovering beside a star](backgrounds/06-shkadov.webp)](backgrounds/06-shkadov.webp) |
| A road to orbit: a hair-fine space elevator climbing out of the atmosphere at sunrise. | Moving a solar system: a Shkadov Thruster mirror millions of kilometres wide reflecting starlight to push an entire star across the galaxy. |

| Star Lifter | Dyson |
| --- | --- |
| [![Star Lifter: machines pulling a column of plasma out of a star](backgrounds/07-lifter.webp)](backgrounds/07-lifter.webp) | [![Dyson: a Dyson sphere under construction, starlight escaping through its gaps](backgrounds/08-dyson.webp)](backgrounds/08-dyson.webp) |
| Harvesting a star: a ring of machines pulls a twisting column of plasma out of its surface. | A star being enclosed: a Dyson sphere two-thirds built, its light escaping through the gaps. |

| Gate | |
| --- | --- |
| [![Gate: a ring-shaped gate showing a distant galaxy through folded space](backgrounds/09-gate.webp)](backgrounds/09-gate.webp) | |
| A gate between galaxies: through the ring, space folds into a tunnel to a distant spiral. | |

### Resolution and displays

Every wallpaper is a single continuous **3840 × 2160** (16:9) WebP image with no stitching or seams. Ultrawide, 16:10 and portrait screens crop cleanly around the central subject. [ASSETS.md](ASSETS.md) records dimensions, provenance and upscaling.

## Palette checks

The palette is held to 30 checks covering contrast, simulated red–green separation and text over the wallpapers at the lock screen's and launcher's modeled opacity.

| Measurement | Recorded result |
| --- | --- |
| Main text on the background | 15.5:1 |
| Weakest terminal signal color | 6.07:1 |
| Selected text | 9.82:1 |
| Muted text on the background | 4.54:1 |
| Red vs green, deuteranopia | 0.128 (target 0.10) |

[DESIGN.md](DESIGN.md) explains where each color comes from: the accent is the accretion disk, the active window border runs blue to amber to red like the Doppler shift across it, and the signal colors are redshift, aurora, fusion plasma and the rest.

## Credits and license

The wallpapers are AI-generated; [ASSETS.md](ASSETS.md) and [GENERATION.md](GENERATION.md) record their provenance, prompts and upscaling. The palette, the scripts and the written notes are original work.

Released under the [MIT license](LICENSE).
