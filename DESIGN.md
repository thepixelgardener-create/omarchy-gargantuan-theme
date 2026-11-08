# Gargantuan design notes

Gargantuan is a dark Omarchy theme about the largest things a civilisation could build or meet: a fusion reactor, a planet opened to its core, a world of water, a space elevator, a ringed giant, a machine that mines a star, a Dyson sphere, a gate to another galaxy and a supermassive black hole. The nine wallpapers climb the Kardashev scale in that order, from mastering a star in a bottle to standing beside the gravity of a billion suns.

This file is the contract for the palette. If a value changes, the rule it follows should still hold, and the values below should be measured again.

## Goals

1. Every terminal color is readable as text: at least 4.5:1 against the background.
2. Red and green stay distinguishable for people with red-green color blindness.
3. Every color comes from something physical in the wallpapers.
4. Ship only what Omarchy can't generate well itself, so new Omarchy versions keep working.

## The rules

**Space is the ground.** The background is the blue-black of deep space, nearly neutral (OKLCH chroma 0.020). Surfaces, muted text and inactive borders stay close to it so that they recede, the way the dark fills most of every wallpaper.

**Starlight is the text.** The foreground is a warm white, the color of sunlight from a star like ours rather than a screen's blue-white. It is light seen against darkness, not a color in its own right (chroma 0.017).

**The accretion disk is the accent.** Amber `#f2a541` is the hot gas at the inner edge of the disk in the black hole wallpaper, the brightest thing in the theme's universe. Focus should come forward, and amber is the color that does on a blue-black ground.

**Doppler shift is the active border.** A disk around a black hole is brighter and bluer on the side rushing toward you and dimmer and redder on the side moving away. The active window border runs the same way: blue, then amber, then red, at 45°. The one moving element of the desktop shows the one motion you can see in the picture.

**Selection is the night side.** Selected text sits on a dark indigo, the shadowed side of a planet, dim enough that all text on it stays readable and blue enough to stand apart from the amber focus.

**Opposites need a second difference.** Red and green look alike to red-green colorblind eyes, so green is made much brighter than red (11.3:1 against 6.1:1 on the background). The difference survives the simulations below.

## Where each color comes from

| Color | Physical source | Role in the theme |
|---|---|---|
| Red | Redshift, light from things moving away | Errors |
| Orange | The molten outer core | Numbers and constants |
| Yellow | Sunlight on a planet's day side | Warnings |
| Green | Aurora in a planet's upper atmosphere | Success and additions |
| Cyan | The light along the gate's inner rim | Types, escapes |
| Blue | Blueshift, light from things moving closer | Information and links |
| Magenta | Hydrogen plasma glowing in the fusion reactor | Keywords |
| Brown | Rock of a planet's crust and of the asteroid belt | Secondary text accents |

## Palette

| Key | Role | Value |
|---|---|---|
| `background` | Main surface, deep space | `#0a0d16` |
| `dark_background` | Side panels, status lines | `#070910` |
| `darker_background` | Deepest surface | `#03050a` |
| `lighter_background` | Cursor line, cards | `#151a28` |
| `foreground` | Text, starlight | `#ebe5d9` |
| `light_foreground` | Secondary text | `#f4efe6` |
| `dark_foreground` | Dim text, line numbers | `#aca69b` |
| `bright_foreground` | Cursor, selected text | `#fffaf2` |
| `muted` | Comments, dividers, inactive borders | `#737a8f` |
| `accent` | Accretion amber: focus, highlights | `#f2a541` |
| `selection` | Night-side indigo | `#2b3354` |
| `red` | Redshift: errors | `#ec6464` |
| `orange` | Molten core: numbers | `#f29350` |
| `yellow` | Sunlight: warnings | `#f0c35e` |
| `green` | Aurora: success | `#84d892` |
| `cyan` | Gate light | `#4cc2d6` |
| `blue` | Blueshift: information | `#729ef2` |
| `magenta` | Fusion plasma | `#b48bf0` |
| `brown` | Crust and asteroid rock | `#b88b66` |

The bright variants keep the same hues and add brightness: `#f59393`, `#f6d78f`, `#ade6b6`, `#83d5e2`, `#9dbcf6` and `#cbaef5`.

## Measured results

The palette is held to 30 checks: palette contrast, red–green separation, signal-color distance, and text over the wallpapers at the modeled 80% lock-screen and 95% launcher background opacity. Black and white bound every sRGB wallpaper pixel, and the foreground is brighter than any overlay can get, so a white wallpaper pixel gives the lowest text contrast. These checks do not inspect composition or cropping.

| Check | Result | Target |
|---|---|---|
| Text on background | 15.5:1 | 7:1 |
| Weakest terminal color | 6.07:1 (red) | 4.5:1 |
| Muted on background | 4.54:1 | 3:1 |
| Dim text on background | 8.02:1 | 4.5:1 |
| Accent on background | 9.46:1 | 4.5:1 |
| Accent on the cursor line | 8.46:1 | 4.5:1 |
| Background text on the accent (selected menu item) | 9.46:1 | 4.5:1 |
| Selected text | 9.82:1 | 4.5:1 |
| Weakest terminal color on the selection | 3.86:1 (red) | 3:1 |
| Lock screen text, white wallpaper bound | 8.60:1 | 4.5:1 |
| Launcher text, white wallpaper bound | 14.0:1 | 4.5:1 |
| Red vs green, deuteranopia | 0.128 | 0.10 |
| Red vs green, protanopia | 0.250 | 0.10 |
| Closest signal pair (blue/magenta) | 0.096 | 0.07 |

Every one of the fourteen standard and bright terminal colors reaches at least 6:1 on the background. Contrast uses WCAG 2; colorblind views use the Machado 2009 simulation at full severity; distances are measured in OKLab. The two distance thresholds are the working choices Farbenlehre made after comparing about 80 Omarchy themes, not a standard.

## Known trade-offs

- The accent, orange and yellow are neighbours. Amber leads because it is the theme's light source; orange and yellow stay apart from it in lightness.
- The active-border gradient also reaches the shell's popups, notifications, menus and lock screen, because Omarchy uses the Hyprland border for them, so red appears in borders that are not errors.
- Blue and magenta are the closest signal pair. Both stay well clear of the threshold, and they keep their distinct physical sources.

## Span wallpapers

Each wallpaper also comes as a span across three monitors: the wallpaper itself on the main screen, and a left and a right panel that continue the scene past the bezels. Omarchy's own background service shows one image on every screen, so the spans need the separate [Panomarchy](https://github.com/thepixelgardener-create/panomarchy) plugin, which finds a wallpaper's panels in `backgrounds/spans/<name>/`. Without it the theme is complete and every wallpaper an ordinary one. README.md explains the layout.

## What the theme ships, and what it leaves to Omarchy

Shipped: `colors.toml`, `icons.theme`, nine wallpapers in `backgrounds/`, their span panels and their `layout.json` in `backgrounds/spans/`, three-screen previews in `previews/`, the scripts that built the spans in `tools/` and these notes. The plugin that shows the spans lives in its own repository.

Left to Omarchy's templates on purpose: the terminal configs, Neovim, VS Code, btop, Chromium, the shell and Hyprland. Omarchy generates them from `colors.toml`, and the checks above cover the colors those templates use. Omarchy also drops `.lua` files, terminal configs and `vscode.json` from themes installed through git, so shipping them would not work anyway.

## Release checklist

1. Measure the palette again: contrast, red–green separation and the wallpaper overlay bounds still meet the targets above.
2. Inspect the wallpapers and their provenance in ASSETS.md.
3. Push, then install from the clean URL: `omarchy theme install <repo-url>`.
4. Look at a terminal with `git diff`, Neovim, btop, the Omarchy menu, a notification and the lock screen.
5. With the Panomarchy plugin enabled, step through all nine wallpapers on three screens and check that every panel lines up at the bezels.
6. Redraw the previews with `tools/build.py --previews` after any wallpaper or panel changes.
