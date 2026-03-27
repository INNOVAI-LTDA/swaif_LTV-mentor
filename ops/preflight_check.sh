#!/usr/bin/env bash
set -euo pipefail

echo "[BMAD preflight] checking required paths..."
required=(
  "ops/prompts"
  "ops/state/workflow_state.sample.json"
)
for p in "${required[@]}"; do
  if [ ! -e "$p" ]; then
    echo "Missing: $p"
    exit 1
  fi
done

echo "[BMAD preflight] project-context check..."
if [ -f "_bmad-output/project-context.md" ]; then
  echo "Found _bmad-output/project-context.md"
else
  echo "Warning: _bmad-output/project-context.md missing"
fi

echo "[BMAD preflight] ok"
