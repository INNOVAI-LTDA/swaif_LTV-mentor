#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <workflow> <batch> <phase> [--dry-run]"
  exit 1
fi

workflow="$1"
batch="$2"
phase="$3"
dry_run="${4:-}"

python ops/run_bmad_phase.py --workflow "$workflow" --batch "$batch" --phase "$phase" ${dry_run:+--dry-run}
