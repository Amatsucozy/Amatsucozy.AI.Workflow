#!/usr/bin/env python3
"""Extract compiler diagnostics from Roslyn SARIF logs into the run-build report table.

Pairs with:
    find . -path '*/obj/msbuild.sarif' -delete 2>/dev/null
    dotnet build <target> -v q -nologo -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1" \
        > /tmp/build-console.txt 2>&1; echo "exit:$?"; tail -8 /tmp/build-console.txt
    python3 sarif_report.py --root .

Scope: Roslyn (CSC) diagnostics only. MSBuild-level failures (restore, SDK,
bad references) never reach SARIF — the caller handles those via the gap rule
in run-build/SKILL.md.

Stdlib only. Exit codes: 0 = no errors, 1 = errors, 2 = no SARIF files found.
"""

import argparse
import glob
import json
import os
import sys
from urllib.parse import unquote, urlparse

# Codes that usually cascade from an earlier missing-type/namespace failure.
CASCADE_CODES = {"CS0246", "CS0234", "CS0400", "CS0103", "CS1061", "CS0117",
                 "CS0115", "CS0538", "CS0535"}

def uri_to_rel(uri: str, root: str) -> str:
    if not uri:
        return "<no file>"
    if uri.startswith("file:"):
        p = unquote(urlparse(uri).path)
        # windows file URIs arrive as /C:/...
        if len(p) > 2 and p[0] == "/" and p[2] == ":":
            p = p[1:]
    else:
        p = unquote(uri)
    try:
        rel = os.path.relpath(os.path.abspath(p), root)
    except ValueError:  # different drive on windows
        rel = p
    return rel.replace("\\", "/")


def load_diagnostics(path: str, root: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARN: unreadable SARIF {path}: {e}", file=sys.stderr)
        return
    for run in doc.get("runs", []):
        for res in run.get("results", []):
            loc = (res.get("locations") or [{}])[0].get("physicalLocation", {})
            region = loc.get("region", {})
            msg = " ".join((res.get("message", {}).get("text") or "").split())
            yield {
                "level": res.get("level", "warning"),
                "code": res.get("ruleId") or "?",
                "file": uri_to_rel(loc.get("artifactLocation", {}).get("uri"), root),
                "line": region.get("startLine", 0),
                "msg": msg,
            }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root; paths reported relative to it")
    ap.add_argument("--pattern", default="**/obj/**/msbuild.sarif",
                    help="glob for SARIF files under root")
    ap.add_argument("--max", type=int, default=30, help="max error rows in the table")
    ap.add_argument("--warnings", action="store_true", help="also print a warning table")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    files = sorted(
        (p for p in glob.glob(os.path.join(root, args.pattern), recursive=True)
         if os.sep + "bin" + os.sep not in p),
        key=os.path.getmtime,  # compile sequence proxy: earlier project first
    )
    if not files:
        print("SARIF: no log files found — build did not run with "
              '-p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1", or was cleaned.')
        return 2

    seen, errors, warnings = set(), [], []
    for path in files:
        for d in load_diagnostics(path, root):
            key = (d["code"], d["file"], d["line"], d["msg"])
            if key in seen:  # multi-target / multi-run duplicates
                continue
            seen.add(key)
            (errors if d["level"] == "error" else warnings).append(d)

    print(f"SARIF: {len(files)} log(s) — {len(errors)} error(s), "
          f"{len(warnings)} warning(s) after dedupe")

    if errors:
        shown = errors[: args.max]
        print()
        print("| # | File | Line | Code | Message |")
        print("|---|------|------|------|---------|")
        for i, d in enumerate(shown, 1):
            print(f"| {i} | {d['file']} | {d['line']} | {d['code']} | {d['msg']} |")
        first = errors[0]
        print()
        print(f"First error: {first['file']}({first['line']}): "
              f"{first['code']}: {first['msg']}")
        tail = errors[1:]
        cascade = sum(1 for d in tail if d["code"] in CASCADE_CODES)
        if tail:
            verdict = ("likely cascade — fix #1 first"
                       if cascade >= max(1, len(tail) // 2)
                       else "mostly independent errors")
            print(f"Cascade check: {cascade}/{len(tail)} subsequent errors are "
                  f"missing-type/member codes — {verdict}")
        if len(errors) > args.max:
            print(f"Truncated: first {args.max} of {len(errors)} — "
                  "rebuild the failing project in isolation for the rest")
        else:
            print("Truncated: none")

    if args.warnings and warnings:
        print()
        print("| # | File | Line | Code | Warning |")
        print("|---|------|------|------|---------|")
        for i, d in enumerate(warnings[: args.max], 1):
            print(f"| {i} | {d['file']} | {d['line']} | {d['code']} | {d['msg']} |")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())