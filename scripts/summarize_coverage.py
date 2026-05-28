#!/usr/bin/env python3
"""Extract source-only line/branch coverage from a coverage.json file.

Usage: summarize_coverage.py <coverage.json> [--src-prefix PREFIX ...]

Source prefixes default to common src layouts. Files whose path starts with
any of the configured "test" prefixes are excluded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEST_PREFIXES = ("tests/", "test/", "tests\\", "test\\")


def is_source_file(path: str, src_prefixes: tuple[str, ...]) -> bool:
    if any(path.startswith(p) for p in TEST_PREFIXES):
        return False
    if not src_prefixes:
        return True
    return any(path.startswith(p) for p in src_prefixes)


def summarize(cov_path: Path, src_prefixes: tuple[str, ...]) -> dict:
    data = json.loads(cov_path.read_text())
    files = data.get("files", {})
    tot_statements = tot_missing = tot_branches = tot_partial = tot_covered_branches = 0
    file_rows = []
    for fname, fdata in files.items():
        if not is_source_file(fname, src_prefixes):
            continue
        s = fdata["summary"]
        tot_statements += s.get("num_statements", 0)
        tot_missing += s.get("missing_lines", 0)
        tot_branches += s.get("num_branches", 0)
        tot_partial += s.get("num_partial_branches", 0)
        tot_covered_branches += s.get("covered_branches", 0)
        file_rows.append((fname, s))

    line_cov = (
        100.0 * (tot_statements - tot_missing) / tot_statements if tot_statements else 0.0
    )
    branch_cov = (
        100.0 * tot_covered_branches / tot_branches if tot_branches else 0.0
    )

    return {
        "files_counted": len(file_rows),
        "statements": tot_statements,
        "missing_lines": tot_missing,
        "branches": tot_branches,
        "partial_branches": tot_partial,
        "covered_branches": tot_covered_branches,
        "line_coverage_pct": round(line_cov, 2),
        "branch_coverage_pct": round(branch_cov, 2),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("coverage_json", type=Path)
    p.add_argument(
        "--src-prefix",
        action="append",
        default=[],
        help="Path prefix(es) considered source. May be repeated.",
    )
    p.add_argument(
        "--label",
        default=None,
        help="Optional label to print alongside the result.",
    )
    args = p.parse_args()

    result = summarize(args.coverage_json, tuple(args.src_prefix))
    if args.label:
        result["label"] = args.label
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
