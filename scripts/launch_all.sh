#!/bin/bash
# Open 9 iTerm tabs (one per worktree) running each worktree's start.sh.
# NB: the app scripts as "iTerm" (not "iTerm2") on this machine — iTerm v3.x.
# Each tab launches claude --permission-mode auto --model claude-opus-4-7
# with the worktree's prompt as the initial user message.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

WORKTREES=(
  "itsdangerous/wt-oneshot"
  "itsdangerous/wt-iter2"
  "itsdangerous/wt-iter20"
  "httpx/wt-oneshot"
  "httpx/wt-iter2"
  "httpx/wt-iter20"
  "requests/wt-oneshot"
  "requests/wt-iter2"
  "requests/wt-iter20"
)

# Build the AppleScript dynamically so each tab knows its own path.
tmpscript="$(mktemp -t llmbench_launcher).scpt"
{
  echo 'tell application "iTerm"'
  echo '    activate'
  echo '    set newWindow to (create window with default profile)'
  echo '    tell newWindow'
  first=1
  for wt in "${WORKTREES[@]}"; do
    path="$ROOT/$wt"
    name="$wt"
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

echo "Launcher AppleScript written to: $tmpscript"
echo "Opening 9 iTerm tabs..."
osascript "$tmpscript"
echo "Launched. Tabs are named '<repo>/<policy>'."
