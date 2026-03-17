#!/bin/bash

# Update script for defuddle skill
# This script clones the latest mz1999/defuddle, builds it, and copies the dist files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/../plugins/defuddle/skills/defuddle/scripts/dist"
TEMP_DIR="/tmp/defuddle-update-$$"

REPO_URL="https://github.com/mz1999/defuddle.git"

echo "=== Defuddle Skill Updater ==="
echo ""

# 1. Clone the repo
echo "[1/5] Cloning defuddle repository..."
rm -rf "$TEMP_DIR"
git clone --depth 1 "$REPO_URL" "$TEMP_DIR"

# 2. Install dependencies
echo "[2/5] Installing dependencies..."
cd "$TEMP_DIR"
npm install

# 3. Build
echo "[3/5] Building defuddle..."
npm run build

# 4. Copy dist files
echo "[4/5] Copying dist files to skill..."
rm -rf "$DIST_DIR"
cp -r "$TEMP_DIR/dist" "$DIST_DIR"

# Get version before cleanup
VERSION=$(cat "$TEMP_DIR/package.json" 2>/dev/null | grep '"version"' | head -1 | sed -E 's/.*"version": "([^"]+)".*/\1/' || echo "unknown")

# 5. Cleanup
echo "[5/5] Cleaning up..."
rm -rf "$TEMP_DIR"

echo ""
echo "=== Update Complete ==="
echo "Defuddle version: $VERSION"
echo ""
echo "Next steps:"
echo "1. Test: export DEFUDDLE_PROXY=... && node plugins/defuddle/skills/defuddle/scripts/defuddle.mjs parse https://example.com --md"
echo "2. Update version table in README.md"
echo "3. Commit: git add plugins/defuddle/skills/defuddle/scripts/dist/ && git commit -m \"Update defuddle to $VERSION\""
echo ""
