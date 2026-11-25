#!/usr/bin/env bash
# Local build: out/Skip Launcher.zip + out/skip-launcher-vX.Y.Z.zip
# Usage: pnpm run build:zip
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "==> skip-launcher: local build"
pnpm run build

for f in plugin.json package.json main.py LICENSE README.md; do
  [[ -f "${ROOT_DIR}/${f}" ]] || { echo "Missing ${f}" >&2; exit 1; }
done

mkdir -p "${ROOT_DIR}/out"
bash "${ROOT_DIR}/scripts/package-zip-manual.sh"

VERSION=$(node -e "console.log(require('./package.json').version)")
PLUGIN_NAME=$(node -e "console.log(require('./plugin.json').name)")
cp -f "${ROOT_DIR}/out/${PLUGIN_NAME}.zip" "${ROOT_DIR}/out/skip-launcher-v${VERSION}.zip"

echo ""
ls -lh "${ROOT_DIR}"/out/*.zip
echo "Install on Deck: Decky -> Settings -> Install Plugin from ZIP (ask first: see skill sl-deck-install)"
