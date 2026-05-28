#!/bin/bash
# Launch the 9 Run-2 worktree sessions in iTerm2 tabs.
# Prereq: run scripts/setup_run2.py first to materialize worktrees and prompts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

WORKTREES=(
  "itsdangerous/wt-r2-oneshot"
  "itsdangerous/wt-r2-iter2"
  "itsdangerous/wt-r2-iter20"
  "httpx/wt-r2-oneshot"
  "httpx/wt-r2-iter2"
  "httpx/wt-r2-iter20"
  "requests/wt-r2-oneshot"
  "requests/wt-r2-iter2"
  "requests/wt-r2-iter20"
)

# Sanity check: every worktree must exist
for wt in "${WORKTREES[@]}"; do
  if [ ! -d "$ROOT/$wt" ]; then
    echo "Missing worktree: $ROOT/$wt" >&2
    echo "Run scripts/setup_run2.py first." >&2
    exit 1
  fi
  if [ ! -f "$ROOT/$wt/.rex_prompt.md" ]; then
    echo "Missing prompt in $ROOT/$wt — run scripts/setup_run2.py" >&2
    exit 1
  fi
done

tmpscript="$(mktemp -t llmbench_r2_launcher).scpt"
{
  echo 'tell application "iTerm2"'
  echo '    activate'
  echo '    set newWindow to (create window with default profile)'
  echo '    tell newWindow'
  first=1
  for wt in "${WORKTREES[@]}"; do
    path="$ROOT/$wt"
    name="r2 $wt"
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
echo "Opening 9 iTerm tabs for Run 2..."
osascript "$tmpscript"
echo "Launched."
