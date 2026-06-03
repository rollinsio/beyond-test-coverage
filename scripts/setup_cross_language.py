#!/usr/bin/env python3
"""Materialize worktrees + prompts for the cross-language (JS/Go) benchmark.

For each of six cloned repos × three policies, create a git worktree
``wt-r3-<policy>`` (branch ``rex-r3-wt-<policy>``) off the repo's ``base``,
wire up dependencies (symlink ``node_modules`` for npm repos; ``pnpm install
--prefer-offline`` for the zod pnpm monorepo; nothing for Go — the module cache
is global), and write a ``.rex_prompt.md`` assembled from ``prompts/cross-language/``.

Usage:
    python scripts/setup_cross_language.py                 # create worktrees + deps + prompts
    python scripts/setup_cross_language.py --prompts-only  # rewrite prompts only (worktrees must exist)
    python scripts/setup_cross_language.py --repos zod chi # restrict to a subset
"""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = ROOT / "prompts" / "cross-language"
SCORE_PY = ROOT / ".claude" / "skills" / "test-quality" / "scripts" / "score.py"
POLICIES = ("oneshot", "iter2", "iter20")

# Per-repo configuration. tests_dir is BOTH what gets deleted/regenerated and
# what the scorer measures. "." means the whole module (Go: colocated _test.go).
REPOS = {
    "express": {
        "lang": "js", "pkg_mgr": "npm", "tests_dir": "test",
        "source_desc": "the Express 5 HTTP framework — application, router, "
                       "request/response, middleware (lib/)",
        "run_cmd": "npx mocha --reporter dot --check-leaks test/ test/acceptance/",
        "delete_cmd": "git rm -r -q test",
        "framework_primitives":
            "- `supertest`: `request(app).get('/').expect(200, done)` drives the "
            "app in-process over real HTTP — no network, no mocks. Baseline uses it heavily.\n"
            "- `node:assert` strict: `assert.strictEqual`, `assert.deepStrictEqual`, "
            "`assert.throws(fn, /regex/)`.",
    },
    "jsonwebtoken": {
        "lang": "js", "pkg_mgr": "npm", "tests_dir": "test",
        "source_desc": "the jsonwebtoken library — sign / verify / decode "
                       "(index.js, sign.js, verify.js, decode.js, lib/)",
        "run_cmd": "npx mocha",
        "delete_cmd": "git rm -r -q test",
        "framework_primitives":
            "- Chai BDD: `expect(x).to.equal(...)`, `.to.throw(ErrType)`, "
            "`.to.deep.equal(...)`, `.to.have.property(...)`.\n"
            "- `sinon.useFakeTimers()` to control time for exp/nbf/iat claim tests — "
            "legitimate (you cannot test expiry without it), and scored as C.2 not C.1.",
    },
    "zod": {
        "lang": "js", "pkg_mgr": "pnpm", "tests_dir": "packages/zod/src",
        "source_desc": "the Zod v4 schema-validation library (packages/zod/src) — "
                       "schema parsing, refinements, coercion, error formatting",
        # vitest reads the workspace config at the repo root; --project zod scopes it.
        "run_cmd": "npx vitest run --project zod",
        # delete only the colocated *.test.ts, never the source they sit beside.
        "delete_cmd": "git rm -r -q $(git ls-files 'packages/zod/src/**/*.test.ts')",
        "framework_primitives":
            "- Vitest: `expect(x).toEqual(...)`, `.toThrow(...)`, and especially "
            "`expect(err).toMatchInlineSnapshot(...)` for error shapes — baseline uses snapshots heavily.\n"
            "- Pure logic: no mocking needed or wanted.",
    },
    "chi": {
        "lang": "go", "pkg_mgr": "go", "tests_dir": ".",
        "source_desc": "the go-chi/chi v5 HTTP router — mux.go, tree.go, middleware/",
        "run_cmd": "go test ./...",
        "delete_cmd": "git rm -r -q $(git ls-files '*_test.go')",
        "framework_primitives":
            "- `net/http/httptest`: `httptest.NewServer`, `httptest.NewRequest`, "
            "`httptest.NewRecorder` exercise handlers/routing in-process. Baseline uses it throughout.\n"
            "- Table-driven subtests: `t.Run(tc.name, func(t *testing.T){...})` over a `[]struct{}`.",
    },
    "gjson": {
        "lang": "go", "pkg_mgr": "go", "tests_dir": ".",
        "source_desc": "the tidwall/gjson JSON path-query library — Get/Parse/Result (gjson.go)",
        "run_cmd": "go test ./...",
        "delete_cmd": "git rm -r -q $(git ls-files '*_test.go')",
        "framework_primitives":
            "- Pure parsing: no I/O, no mocks. Use table-driven `t.Run` subtests.\n"
            "- `testing.F` fuzz targets are fair game for path/parse robustness.",
    },
    "golang-jwt": {
        "lang": "go", "pkg_mgr": "go", "tests_dir": ".",
        "source_desc": "the golang-jwt/jwt v5 library — token parse/sign/verify, "
                       "signing methods (HMAC/RSA/ECDSA/EdDSA)",
        "run_cmd": "go test ./...",
        "delete_cmd": "git rm -r -q $(git ls-files '*_test.go')",
        "framework_primitives":
            "- Table-driven `t.Run` subtests over fixed token strings.\n"
            "- `errors.Is` / `errors.As` for the typed error sentinels — not message substrings.",
    },
    # ── Kotlin + Swift targets ────────────────────────────────────────────────
    # Configured for parity with the JS/Go targets; the generation arms have NOT
    # been run yet (they need the Kotlin/Swift toolchains). run_cmd/delete_cmd are
    # the conventional commands — confirm against each repo's build before a run.
    # main() skips any target whose <repo>/base clone is absent, so these stay
    # inert until you clone them (see .gitignore for the canonical clone dirs).
    "kotlinx-serialization": {
        "lang": "kotlin", "pkg_mgr": "gradle", "tests_dir": ".",
        "repo_url": "https://github.com/Kotlin/kotlinx.serialization",
        "source_desc": "the kotlinx.serialization library — JSON/CBOR/ProtoBuf "
                       "encoding, schema descriptors, polymorphism (core/, formats/)",
        "run_cmd": "./gradlew jvmTest",
        "delete_cmd": "git rm -r -q $(git ls-files '*/commonTest/*' '*/jvmTest/*' '*Test.kt')",
        "framework_primitives":
            "- kotlin.test `assertEquals(expected, actual)` — expected FIRST; "
            "triple-quoted `\"\"\"{…}\"\"\"` literals for JSON/CBOR vectors.\n"
            "- `assertFailsWith<T> { }` for typed errors; some Kotest `should(\"…\") { }`. "
            "Pure logic — no mocks.",
    },
    "kotlinx-datetime": {
        "lang": "kotlin", "pkg_mgr": "gradle", "tests_dir": ".",
        "repo_url": "https://github.com/Kotlin/kotlinx-datetime",
        "source_desc": "the kotlinx-datetime library — Instant / LocalDate(Time) / "
                       "TimeZone / UtcOffset arithmetic & ISO parsing (core/)",
        "run_cmd": "./gradlew jvmTest",
        "delete_cmd": "git rm -r -q $(git ls-files '*/common/test/*' '*/commonTest/*' '*Test.kt')",
        "framework_primitives":
            "- kotlin.test `@Test` + `assertEquals`; boundary-heavy date arithmetic.\n"
            "- Pin ISO-8601 string vectors (`\"PT0.999999999S\"`); don't recompute via the API.",
    },
    "kotlin-result": {
        "lang": "kotlin", "pkg_mgr": "gradle", "tests_dir": ".",
        "repo_url": "https://github.com/michaelbull/kotlin-result",
        "source_desc": "the kotlin-result library — Result<V, E> monad: "
                       "map/and/or/unwrap/binding (kotlin-result/, kotlin-result-coroutines/)",
        "run_cmd": "./gradlew jvmTest",
        "delete_cmd": "git rm -r -q $(git ls-files '*/commonTest/*')",
        "framework_primitives":
            "- kotlin.test `@Test` in nested grouping classes; `assertFailsWith<T> { }`.\n"
            "- kotlinx-coroutines-test `runTest { }` is how a `suspend` fun is tested (C.2, not a mock).",
    },
    "swift-argument-parser": {
        "lang": "swift", "pkg_mgr": "swift", "tests_dir": ".",
        "repo_url": "https://github.com/apple/swift-argument-parser",
        "source_desc": "the swift-argument-parser library — declarative CLI parsing, "
                       "validation, help/usage generation (Sources/ArgumentParser)",
        "run_cmd": "swift test",
        "delete_cmd": "git rm -r -q $(git ls-files 'Tests/*')",
        "framework_primitives":
            "- XCTest `XCTAssertThrowsError(try …) { … }` for typed errors.\n"
            "- The `AssertErrorMessage(_, _, \"full message\")` helper pins exact error text "
            "(a documented contract here) — prefer the error type otherwise.",
    },
    "swift-collections": {
        "lang": "swift", "pkg_mgr": "swift", "tests_dir": ".",
        "repo_url": "https://github.com/apple/swift-collections",
        "source_desc": "the swift-collections package — Deque, OrderedSet/Dictionary, "
                       "BitSet/BitArray, TreeDictionary/Set, Heap (Sources/)",
        "run_cmd": "swift test",
        "delete_cmd": "git rm -r -q $(git ls-files 'Tests/*')",
        "framework_primitives":
            "- The StdlibUnittest-style `expectEqual` / `expectEqualElements` harness "
            "(CollectionsTestSupport) — the project's XCTest wrappers.\n"
            "- Swift Testing `@Test` / `#expect` (and `@Test(arguments:)`) in the newer suites.",
    },
    "SwiftyJSON": {
        "lang": "swift", "pkg_mgr": "swift", "tests_dir": ".",
        "repo_url": "https://github.com/SwiftyJSON/SwiftyJSON",
        "source_desc": "the SwiftyJSON library — ergonomic JSON access/mutation "
                       "over Any, typed getters, literal conformances (Source/SwiftyJSON)",
        "run_cmd": "swift test",
        "delete_cmd": "git rm -r -q $(git ls-files 'Tests/*')",
        "framework_primitives":
            "- XCTest `XCTAssertEqual(actual, \"literal\")` — literal LAST.\n"
            "- Pin parsed values as fixed literals; compare JSON via `XCTAssertEqual(JSON(a), JSON(b))`.",
    },
}

VERIFY_CMD = {
    "js": "`node -e '...'` for a quick out-of-band check",
    "go": "a scratch `package main` run with `go run`, or `go test -run` a throwaway",
    "kotlin": "`kotlin -e '...'`, a `jshell` snippet for JVM stdlib, or a throwaway `@Test` you delete",
    "swift": "`swift -e '...'` or a scratch test you delete",
}


def _score_paths(meta: dict, wt: Path, base: Path) -> tuple[str, str]:
    td = meta["tests_dir"]
    gen = str(wt) if td == "." else str(wt / td)
    bas = str(base) if td == "." else str(base / td)
    return gen, bas


def build_prompt(repo: str, policy: str, parts: dict[str, str], label: str) -> str:
    meta = REPOS[repo]
    wt = ROOT / repo / f"wt-{label}-{policy}"
    base = ROOT / repo / "base"
    gen_path, base_path = _score_paths(meta, wt, base)
    lang = meta["lang"]
    score_cmd = (f"python {SCORE_PY} --lang {lang} "
                 f"--tests {gen_path} --baseline {base_path}")
    score_cmd_baseline = (f"python {SCORE_PY} --lang {lang} --tests {base_path} "
                          f"--json > .rex_metrics/baseline_scorecard.json")

    if meta["pkg_mgr"] == "npm":
        env_note = ("`node_modules/` is symlinked from `../base/node_modules` "
                    "(already installed). `npx <tool>` resolves through it.")
    elif meta["pkg_mgr"] == "pnpm":
        env_note = ("This is a pnpm monorepo. `node_modules/` has been relinked "
                    "from the shared pnpm store (no download). Run vitest from the "
                    "worktree root; the workspace config is picked up automatically.")
    elif meta["pkg_mgr"] == "gradle":
        env_note = ("Gradle resolves dependencies from its shared cache (network on "
                    "first run); nothing is pre-linked. Run `./gradlew` from the "
                    "worktree root.")
    elif meta["pkg_mgr"] == "swift":
        env_note = ("SwiftPM resolves and builds from the worktree on first "
                    "`swift test`; the package cache is shared. Nothing is pre-linked.")
    else:
        env_note = ("Go module cache is shared globally; `go test` resolves "
                    "offline. There is nothing to install.")

    mapping = {
        "REPO": repo, "POLICY": policy, "LANG": lang,
        "WORKTREE": str(wt), "BASE": str(base),
        "SOURCE_DESC": meta["source_desc"], "TESTS_DIR": meta["tests_dir"],
        "DELETE_CMD": meta["delete_cmd"], "RUN_CMD": meta["run_cmd"],
        "SCORE_CMD": score_cmd, "SCORE_CMD_BASELINE": score_cmd_baseline,
        "VERIFY_CMD": VERIFY_CMD[lang], "ENV_NOTE": env_note,
        "FRAMEWORK_PRIMITIVES": meta["framework_primitives"],
    }
    body = (parts["common_header"] + "\n" + parts["quality_contract"] + "\n"
            + parts["quality_scorecard"] + "\n" + parts[policy])
    for k, v in mapping.items():
        body = body.replace("{" + k + "}", v)
    return body


def create_worktree(repo: str, policy: str, label: str) -> Path:
    base = ROOT / repo / "base"
    wt = ROOT / repo / f"wt-{label}-{policy}"
    branch = f"rex-{label}-wt-{policy}"
    if wt.exists():
        print(f"  worktree exists: {wt}")
        return wt
    existing = subprocess.run(["git", "-C", str(base), "branch", "--list", branch],
                              check=True, capture_output=True, text=True).stdout.strip()
    args = ["git", "-C", str(base), "worktree", "add"]
    args += [str(wt), branch] if existing else [str(wt), "-b", branch]
    subprocess.run(args, check=True)
    return wt


def setup_deps(repo: str, wt: Path) -> None:
    meta = REPOS[repo]
    if meta["pkg_mgr"] == "npm":
        link = wt / "node_modules"
        if not link.exists():
            os.symlink(ROOT / repo / "base" / "node_modules", link)
            print(f"  linked node_modules -> base ({repo})")
    elif meta["pkg_mgr"] == "pnpm":
        if not (wt / "node_modules").exists():
            print(f"  pnpm install --prefer-offline ({repo}/{wt.name}) ...")
            subprocess.run(["pnpm", "install", "--prefer-offline", "--silent"],
                           cwd=str(wt), check=True)
    # go / gradle / swift: nothing to pre-link — each resolves from its own
    # shared cache (Go module cache, Gradle cache, SwiftPM cache) on first run.


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts-only", action="store_true",
                    help="Only (re)write prompts; worktrees + deps must already exist.")
    ap.add_argument("--label", default="r3", help="wt-<label>-<policy> (default r3).")
    ap.add_argument("--repos", nargs="*", default=list(REPOS),
                    help="Subset of repos (default: all configured targets).")
    args = ap.parse_args()

    parts = {name: (PROMPT_DIR / f"{name}.md").read_text() for name in
             ("common_header", "quality_contract", "quality_scorecard",
              "oneshot", "iter2", "iter20")}

    written = []
    for repo in args.repos:
        if repo not in REPOS:
            print(f"  unknown repo: {repo}", file=sys.stderr)
            continue
        if not (ROOT / repo / "base").exists():
            url = REPOS[repo].get("repo_url", "<repo>")
            print(f"  SKIP (clone not on disk): clone {url} into "
                  f"{ROOT / repo / 'base'} first")
            continue
        for policy in POLICIES:
            wt = ROOT / repo / f"wt-{args.label}-{policy}"
            if not args.prompts_only:
                wt = create_worktree(repo, policy, args.label)
                setup_deps(repo, wt)
            elif not wt.exists():
                print(f"  SKIP (missing worktree): {wt}")
                continue
            (wt / ".rex_metrics").mkdir(exist_ok=True)
            prompt = build_prompt(repo, policy, parts, args.label)
            (wt / ".rex_prompt.md").write_text(prompt)
            start = wt / "start.sh"
            start.write_text(f'#!/bin/bash\nset -euo pipefail\ncd "{wt}"\n'
                             f'exec claude --permission-mode auto "$(cat .rex_prompt.md)"\n')
            start.chmod(start.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            written.append(str(wt))

    print(f"\nCross-language experiment ready: {len(written)} worktrees configured.")
    for w in written:
        print(f"  {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
