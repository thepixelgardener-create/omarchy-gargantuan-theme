#!/usr/bin/env bash
# Copy the theme's files (not the build tooling or work/) into Omarchy's user
# themes, for testing before a push. Users install with `omarchy theme install`.
set -euo pipefail
src=$(cd "$(dirname "$0")/.." && pwd)
dst="$HOME/.config/omarchy/themes/gargantuan"
mkdir -p "$dst"
rsync -a --delete --delete-excluded \
  --include='/colors.toml' --include='/icons.theme' --include='/preview.*' \
  --include='/backgrounds/***' --exclude='*' \
  "$src/" "$dst/"
echo "installed to $dst"
