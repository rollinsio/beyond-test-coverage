#!/bin/bash
# Launch the 9 quality-experiment worktree sessions in iTerm tabs.
# NB: the app scripts as "iTerm" (not "iTerm2") on this machine — iTerm v3.x.
# Prereq: run scripts/setup_quality.py first to materialize worktrees and prompts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Optional first arg = worktree label (default r2 → wt-r2-*, the quality experiment).
# Use r2b for the ablation arm (wt-r2b-*, same prompts on Opus 4.7).
LABEL="${1:-r2}"

WORKTREES=()
for repo in itsdangerous httpx requests; do
  for pol in oneshot iter2 iter20; do
    WORKTREES+=("$repo/wt-$LABEL-$pol")
  done
done

# Sanity check: every worktree must exist
for wt in "${WORKTREES[@]}"; do
  if [ ! -d "$ROOT/$wt" ]; then
    echo "Missing worktree: $ROOT/$wt" >&2
    echo "Run scripts/setup_quality.py first." >&2
    exit 1
  fi
  if [ ! -f "$ROOT/$wt/.rex_prompt.md" ]; then
    echo "Missing prompt in $ROOT/$wt — run scripts/setup_quality.py" >&2
    exit 1
  fi
done

tmpscript="$(mktemp -t llmbench_r2_launcher).scpt"
{
  echo 'tell application "iTerm"'
  echo '    activate'
  echo '    set newWindow to (create window with default profile)'
  echo '    tell newWindow'
  first=1
  for wt in "${WORKTREES[@]}"; do
    path="$ROOT/$wt"
    name="$LABEL $wt"
    if [ "$first" = "1" ]; then
      first=0
      cat <<EOF
        tell current session
            set name to "$name"
            write text "cd '$path' && ./start.sh"
        end tell
EOF
    else
      cat <<EOF
        create tab with default profile
        tell current session
            set name to "$name"
            write text "cd '$path' && ./start.sh"
        end tell
EOF
    fi
  done
  echo '    end tell'
  echo 'end tell'
} > "$tmpscript"

echo "Launcher AppleScript at: $tmpscript"
echo "Opening 9 iTerm tabs for the quality experiment..."
osascript "$tmpscript"
echo "Launched."
