# Assets

## Current artwork

Nine cosmic subjects: Gargantuan (black hole), Fusion (reactor), Core (planetary cutaway), Thalassa (ocean planet), Tether (space elevator), Giant (ringed gas giant), Star Lifter (stellar harvesting), Dyson (sphere under construction), and Gate (stargate).

Each scene now has a single continuous panorama. The former independently generated left, main and right panels are retired: no monitor-specific seams or differently enlarged gap regions remain in the new construction.

- `backgrounds/NN-name.webp`: centred 3840 × 2160 single-screen crops.
- `backgrounds/span-NN-name.webp`: 9840 × 3840 continuous panoramas.
- `previews/NN-name.webp`: samples of the actual panorama through the documented three-monitor layout.

The single-screen crop and the main-monitor portion of a span are different framings of the same scene. A panorama adapts to other monitor arrangements through Station's framing; it is no longer composed to place three separately painted images on particular monitors.

## Generation and detail

The built-in image tool generated the new scenes at approximately 2007 × 783 pixels. The approved water-planet repair is retained. GENERATION.md records the prompts.

Real-ESRGAN General x4 v3 processes each new source uniformly with 64-pixel tiles and one processing thread. The export blends 65% enhanced output with 35% Lanczos enlargement. Panoramas are 9840 × 3840, and the 16:9 wallpaper is cropped from the same processed image and reduced to 3840 × 2160. New exports use WebP quality 95; the approved ocean panorama retains its Real-ESRGAN x4plus, quality-92 export.

The General model's NCNN weights come from [Upscayl's model repository](https://github.com/upscayl/custom-models). A GPU timeout during an initial x4plus run produced dark, incomplete tiles despite a successful process exit. That export was rejected. The new exporter checks enhanced dimensions and compares small regions with the source before blending, and writes final files atomically.

These are AI-upscaled exports. Fine texture is synthesized; file dimensions do not imply native 4K detail. Artistic glows, dark space and atmospheric clouds can remain intentionally soft. Increasing zoom still magnifies the source's finite detail.

## License

The repository's MIT license covers the palette, scripts, notes and images. The artwork is AI-generated.
