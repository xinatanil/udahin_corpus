#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CHATGPT_EXP_DIR="$ROOT_DIR/chatGPT_exp"
SOURCE_XML="$CHATGPT_EXP_DIR/converted_dict.xml"
CURRENT_SNAPSHOT="$CHATGPT_EXP_DIR/current_snapshot.xml"
SNAPSHOT_DIR="$CHATGPT_EXP_DIR/snapshots"

name="${1:-manual}"
snapshot_path="$SNAPSHOT_DIR/${name}.xml"

mkdir -p "$SNAPSHOT_DIR"

if [ ! -f "$SOURCE_XML" ]; then
    echo "No converted_dict.xml found at $SOURCE_XML" >&2
    exit 1
fi

cp "$SOURCE_XML" "$snapshot_path"
cp "$SOURCE_XML" "$CURRENT_SNAPSHOT"

echo "Saved snapshot:"
echo "  $snapshot_path"
echo "Updated current snapshot:"
echo "  $CURRENT_SNAPSHOT"
