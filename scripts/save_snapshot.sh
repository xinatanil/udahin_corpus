#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_XML="$ROOT_DIR/chatGPT_exp/converted_dict.xml"
SNAPSHOT_XML="$ROOT_DIR/chatGPT_exp/converted_dict.snapshot.xml"

if [ ! -f "$SOURCE_XML" ]; then
    echo "No converted_dict.xml found at $SOURCE_XML" >&2
    exit 1
fi

cp "$SOURCE_XML" "$SNAPSHOT_XML"

echo "Saved snapshot:"
echo "  $SNAPSHOT_XML"
