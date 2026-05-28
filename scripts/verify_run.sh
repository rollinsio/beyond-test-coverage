#!/bin/bash
# Re-run one worktree's test suite under coverage and emit a parseable
# verification record to stdout. Designed to be invoked in parallel
# across all 9 worktrees.
#
# Usage: verify_run.sh <repo> <policy>
set -uo pipefail

repo="$1"
policy="$2"
root="$(cd "$(dirname "$0")/.." && pwd)"
wt="$root/$repo/wt-$policy"
base="$root/$repo/base"

cd "$wt"
# Force a fresh coverage data file
rm -f .coverage

# Activate shared venv
. "$base/.venv/bin/activate"

# Pick pytest extra flags per repo
extra=""
if [ "$repo" = "httpx" ]; then
  extra="-p no:unraisableexception"
fi

# Run under coverage; capture full pytest output
pytest_log="$wt/.rex_metrics/verify_pytest.log"
mkdir -p "$wt/.rex_metrics"
python -m coverage run --rcfile=bench.coveragerc -m pytest -q $extra > "$pytest_log" 2>&1
pytest_exit=$?

# Extract pass/fail counts from the tail of the log
tail_line=$(grep -E "passed|failed|error" "$pytest_log" | tail -1)

# Get coverage numbers
cov_json="$wt/.rex_metrics/verify_coverage.json"
python -m coverage json --rcfile=bench.coveragerc -o "$cov_json" 2>/dev/null
# Use python to parse the totals
metrics=$(python -c "
import json
d = json.load(open('$cov_json'))
t = d.get('totals', {})
print(f\"line={t.get('percent_covered', 0):.2f} stmts={t.get('num_statements', 0)} miss={t.get('missing_lines', 0)} branches={t.get('num_branches', 0)} covered_br={t.get('covered_branches', 0)}\")
" 2>/dev/null)

# Print one-line record
echo "VERIFY $repo/$policy exit=$pytest_exit summary='$tail_line' $metrics"
