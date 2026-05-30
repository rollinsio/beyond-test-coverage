#!/usr/bin/env python3
"""Materialize the quality-experiment worktrees, prompts, and start.sh files.

These worktrees are named ``wt-r2-<policy>`` so they don't collide with the
coverage-driven control's preserved ``wt-<policy>`` worktrees. Branches are
``rex-r2-wt-<policy>``.

Usage:
    python scripts/setup_quality.py                # creates worktrees + prompts + start.sh
    python scripts/setup_quality.py --prompts-only # just writes prompts/start.sh; worktrees must exist

After running, ``scripts/launch_all.sh`` cannot be reused as-is —
update the worktree list in it (or use ``launch_quality.sh``) to
target the wt-r2-* worktrees.
"""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = ROOT / "prompts" / "quality"

REPOS = {
    "itsdangerous": {
        "package": "itsdangerous",
        "source_dir": "src/itsdangerous",
        "tests_dir": "tests",
        "pytest_extra": "",
        "baseline_pure_line": 97.65,
        "baseline_pure_branch": 94.90,
        "baseline_combined": 97.14,
        "dep_note": (
            "Already installed in the base venv (no need to install again): "
            "pytest, freezegun, coverage, mutmut, and itsdangerous via `pip "
            "install -e .` from the base clone."
        ),
        "framework_primitives": (
            "- `freezegun.freeze_time(...)` — control time for `TimestampSigner` "
            "expiration tests. Used by the baseline.\n"
            "- This package is pure Python with no I/O; there are no MockTransport-style "
            "primitives. Just exercise the public API."
        ),
    },
    "httpx": {
        "package": "httpx",
        "source_dir": "httpx",
        "tests_dir": "tests",
        "pytest_extra": "-p no:unraisableexception",
        "baseline_pure_line": 100.00,
        "baseline_pure_branch": 97.27,
        "baseline_combined": 99.43,
        "dep_note": (
            "Already installed in the base venv via `pip install -r "
            "requirements.txt` (which installed `-e .[brotli,cli,http2,socks,zstd]` "
            "plus pytest, coverage, trio, trustme, etc.)."
        ),
        "framework_primitives": (
            "- `httpx.MockTransport(handler)` — synthesize responses for "
            "`Client`/`AsyncClient`. Used by the baseline extensively.\n"
            "- `httpx.WSGITransport(app)` — in-process WSGI callables.\n"
            "- `httpx.ASGITransport(app)` — in-process ASGI callables.\n"
            "- `monkeypatch` (pytest builtin) — for env-var control.\n"
            "- `trustme` — for TLS test fixtures.\n"
            "- `trio` is installed; use `anyio.run(...)` to exercise async "
            "code paths (no `pytest-anyio` plugin is in the base venv)."
        ),
    },
    "requests": {
        "package": "requests",
        "source_dir": "src/requests",
        "tests_dir": "tests",
        "pytest_extra": "",
        "baseline_pure_line": 87.86,
        "baseline_pure_branch": 79.48,
        "baseline_combined": 85.73,
        "dep_note": (
            "Already installed in the base venv via `pip install -r "
            "requirements-dev.txt` (which installed `-e .[socks]`, pytest, "
            "pytest-httpbin, trustme, etc.)."
        ),
        "framework_primitives": (
            "- `pytest-httpbin` — spawns a local httpbin HTTP server; "
            "request via the `httpbin` fixture (`httpbin('get')` → URL). "
            "**Used by the coverage-driven control's standout suite (`requests/wt-iter20`)** for "
            "integration tests with zero mock LOC.\n"
            "- `monkeypatch` (pytest builtin) — for env-var control "
            "(`REQUESTS_CA_BUNDLE`, etc.).\n"
            "- `trustme` — for TLS test fixtures."
        ),
    },
}
POLICIES = ("oneshot", "iter2", "iter20")


def load_prompt_parts() -> dict[str, str]:
    return {
        "common_header": (PROMPT_DIR / "common_header.md").read_text(),
        "quality_contract": (PROMPT_DIR / "quality_contract.md").read_text(),
        "quality_scorecard": (PROMPT_DIR / "quality_scorecard.md").read_text(),
        "oneshot": (PROMPT_DIR / "oneshot.md").read_text(),
        "iter2": (PROMPT_DIR / "iter2.md").read_text(),
        "iter20": (PROMPT_DIR / "iter20.md").read_text(),
    }


def substitute(text: str, mapping: dict[str, str]) -> str:
    for k, v in mapping.items():
        text = text.replace("{" + k + "}", v)
    return text


def build_prompt(repo: str, policy: str, parts: dict[str, str], label: str) -> str:
    meta = REPOS[repo]
    wt = ROOT / repo / f"wt-{label}-{policy}"
    base = ROOT / repo / "base"
    mapping = {
        "REPO": repo,
        "POLICY": policy,
        "WORKTREE": str(wt),
        "BASE": str(base),
        "PACKAGE": meta["package"],
        "SOURCE_DIR": meta["source_dir"],
        "TESTS_DIR": meta["tests_dir"],
        "PYTEST_EXTRA": meta["pytest_extra"],
        "BL_LINE": f"{meta['baseline_pure_line']:.2f}",
        "BL_BRANCH": f"{meta['baseline_pure_branch']:.2f}",
        "BL_COMBINED": f"{meta['baseline_combined']:.2f}",
        "DEP_NOTE": meta["dep_note"],
        "FRAMEWORK_PRIMITIVES": meta["framework_primitives"],
    }
    body = substitute(
        parts["common_header"]
        + "\n"
        + parts["quality_contract"]
        + "\n"
        + parts["quality_scorecard"]
        + "\n"
        + parts[policy],
        mapping,
    )
    return body


def start_script(worktree: Path, model: str, effort: str) -> str:
    effort_flag = f" --effort {effort}" if effort else ""
    return textwrap.dedent(
        f"""\
        #!/bin/bash
        set -euo pipefail
        cd "{worktree}"
        # bench.coveragerc is copied here by setup_quality.py; don't re-install.
        exec claude --permission-mode auto --model {model}{effort_flag} "$(cat .rex_prompt.md)"
        """
    )


def create_worktree(repo: str, policy: str, label: str) -> Path:
    base = ROOT / repo / "base"
    wt = ROOT / repo / f"wt-{label}-{policy}"
    branch = f"rex-{label}-wt-{policy}"
    if wt.exists():
        print(f"  worktree exists: {wt}")
        return wt
    # Check branch exists
    branches = subprocess.run(
        ["git", "-C", str(base), "branch", "--list", branch],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    args = ["git", "-C", str(base), "worktree", "add"]
    if branches:
        args += [str(wt), branch]
    else:
        args += [str(wt), "-b", branch]
    subprocess.run(args, check=True)
    return wt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts-only", action="store_true",
                    help="Skip worktree creation; only (re)write prompts and start.sh.")
    ap.add_argument("--label", default="r2",
                    help="Worktree/branch label: wt-<label>-<policy> / rex-<label>-wt-<policy>. "
                         "Default 'r2' (the quality experiment, Opus 4.8). Use 'r2b' for the "
                         "ablation arm (same prompts, Opus 4.7).")
    ap.add_argument("--model", default="claude-opus-4-8",
                    help="Model passed to `claude --model` in each start.sh. Default claude-opus-4-8.")
    ap.add_argument("--effort", default="",
                    help="Effort level passed to `claude --effort` (e.g. xhigh). "
                         "Default empty = inherit from settings.")
    args = ap.parse_args()

    parts = load_prompt_parts()
    written = []
    for repo in REPOS:
        for policy in POLICIES:
            if not args.prompts_only:
                wt = create_worktree(repo, policy, args.label)
            else:
                wt = ROOT / repo / f"wt-{args.label}-{policy}"
                if not wt.exists():
                    print(f"  SKIP (worktree missing, use without --prompts-only): {wt}")
                    continue

            # Copy bench.coveragerc into the worktree
            bench = ROOT / repo / "base" / "bench.coveragerc"
            if bench.exists():
                target = wt / "bench.coveragerc"
                target.write_text(bench.read_text())

            # Materialize the prompt
            prompt = build_prompt(repo, policy, parts, args.label)
            (wt / ".rex_prompt.md").write_text(prompt)

            # Materialize start.sh
            start = wt / "start.sh"
            start.write_text(start_script(wt, args.model, args.effort))
            start.chmod(start.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            written.append(str(wt))

    print("\nQuality experiment ready:")
    for w in written:
        print(f"  {w}")
    print(f"\n{len(written)} worktrees configured. "
          f"Launch them with a new launcher (or update scripts/launch_all.sh).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
