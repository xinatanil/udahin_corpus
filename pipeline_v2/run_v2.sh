#!/bin/bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
SCRIPT_DIR="$ROOT_DIR/scripts"
SECONDS=0

format_elapsed() {
    local total_seconds=$1
    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))

    printf '%02d:%02d:%02d' "$hours" "$minutes" "$seconds"
}

mkdir -p "$ROOT_DIR/output"
cd "$SCRIPT_DIR"
bash ./convert_source_dict.sh

elapsed=$SECONDS
echo "pipeline_v2 completed in $(format_elapsed "$elapsed")"
