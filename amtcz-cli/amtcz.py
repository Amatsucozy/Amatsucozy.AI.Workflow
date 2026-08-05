#!/usr/bin/env python3
"""amtcz — standalone CLI for the AMaTsuCoZy SDLC kit (gh/az-style).

The single source of truth for the kit's scripted tooling — the per-skill
scripts it replaced are deleted. Installed machine-level onto PATH:

    pipx install <path-or-git-url>        # preferred, isolated
    pip install --user <path-or-git-url>  # alternative
    py -m pip install --user <...>        # windows launcher

pip generates a native `amtcz` / `amtcz.exe` entry point, so the CLI works
identically in Claude Code sessions, bare CI, and any shell on macOS,
Windows, and Linux. Availability check is mechanical (`command -v amtcz`).
When absent, the workflow STOPS and asks the human: install, or explicitly
approve the degraded verbatim commands for the session (see CLAUDE.md ->
Tooling Resolution).

Terminal safety: ALL output is pure ASCII, unconditionally. Legacy console
codepages (cp1252/cp437 under some pwsh/cmd setups) garble or truncate
non-ASCII stdout; every emitted line passes through one sanitizer, and data
fields degrade non-ASCII characters to '?'. Deterministic on every shell.

Subcommands:

  amtcz sarif build [target] [--root .] [--pattern G] [--max N] [--warnings]
      Clean stale SARIF logs, run `dotnet build -v q -nologo
      -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1"` (console to a temp
      file, last 8 lines echoed), then extract diagnostics.
      exit: 0 = build ok + no errors, 1 = compiler errors,
            2 = no SARIF logs produced, 3 = GAP (build failed but SARIF has
            zero errors -> MSBuild-level failure: restore/SDK/references),
            4 = dotnet not on PATH

  amtcz sarif probe [--root .] [--pattern G] [--max N] [--warnings]
      Extraction only, over SARIF logs already on disk (no build).
      exit: 0 = no errors, 1 = errors, 2 = no SARIF files found

  amtcz exp inventory [--root .]
  amtcz exp search [--root .] [--tag T]... [--symptom S] [--keyword K]... [--max N]
      Experience-memory lookup (CLAUDE.md routing steps 1-2).
      exit: 0 = ran (0 hits is valid), 1 = usage error (no search flags),
            2 = docs/experiences/ has no entries yet

Stdlib only.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from urllib.parse import unquote, urlparse

VERSION = "0.2.0"


def out(line="", err=False):
    """The only output path. Guarantees pure-ASCII bytes on any console."""
    text = str(line).encode("ascii", "replace").decode("ascii")
    print(text, file=sys.stderr if err else sys.stdout)


# ============================================================================
# sarif — Roslyn SARIF build diagnostics
# ============================================================================

# Codes that usually cascade from an earlier missing-type/namespace failure.
CASCADE_CODES = {"CS0246", "CS0234", "CS0400", "CS0103", "CS1061", "CS0117",
                 "CS0115", "CS0538", "CS0535"}

BUILD_PROPERTY = "-p:ErrorLog=obj/msbuild.sarif%2Cversion=2.1"


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
        out(f"WARN: unreadable SARIF {path}: {e}", err=True)
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


def run_probe(root: str, pattern: str, max_rows: int, show_warnings: bool) -> int:
    """Extraction core, shared by `sarif probe` and `sarif build`.
    Exit meaning: 0 no errors, 1 errors, 2 no SARIF files found."""
    files = sorted(
        (p for p in glob.glob(os.path.join(root, pattern), recursive=True)
         if os.sep + "bin" + os.sep not in p),
        key=os.path.getmtime,  # compile sequence proxy: earlier project first
    )
    if not files:
        out("SARIF: no log files found - build did not run with "
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

    out(f"SARIF: {len(files)} log(s) - {len(errors)} error(s), "
        f"{len(warnings)} warning(s) after dedupe")

    if errors:
        shown = errors[:max_rows]
        out()
        out("| # | File | Line | Code | Message |")
        out("|---|------|------|------|---------|")
        for i, d in enumerate(shown, 1):
            out(f"| {i} | {d['file']} | {d['line']} | {d['code']} | {d['msg']} |")
        first = errors[0]
        out()
        out(f"First error: {first['file']}({first['line']}): "
            f"{first['code']}: {first['msg']}")
        tail = errors[1:]
        cascade = sum(1 for d in tail if d["code"] in CASCADE_CODES)
        if tail:
            verdict = ("likely cascade - fix #1 first"
                       if cascade >= max(1, len(tail) // 2)
                       else "mostly independent errors")
            out(f"Cascade check: {cascade}/{len(tail)} subsequent errors are "
                f"missing-type/member codes - {verdict}")
        if len(errors) > max_rows:
            out(f"Truncated: first {max_rows} of {len(errors)} - "
                "rebuild the failing project in isolation for the rest")
        else:
            out("Truncated: none")

    if show_warnings and warnings:
        out()
        out("| # | File | Line | Code | Warning |")
        out("|---|------|------|------|---------|")
        for i, d in enumerate(warnings[:max_rows], 1):
            out(f"| {i} | {d['file']} | {d['line']} | {d['code']} | {d['msg']} |")

    return 1 if errors else 0


def cmd_sarif_probe(args) -> int:
    return run_probe(os.path.abspath(args.root), args.pattern, args.max, args.warnings)


def clean_stale_sarif(root: str) -> int:
    """Delete every msbuild.sarif under an obj/ path (skip bin/, .git,
    node_modules). Cross-platform replacement for the old `find -delete`."""
    removed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in ("bin", ".git", "node_modules")]
        if "msbuild.sarif" in filenames and "obj" in dirpath.split(os.sep):
            try:
                os.remove(os.path.join(dirpath, "msbuild.sarif"))
                removed += 1
            except OSError:
                pass
    return removed


def cmd_sarif_build(args) -> int:
    root = os.path.abspath(args.root)
    clean_stale_sarif(root)

    console = os.path.join(tempfile.gettempdir(), "amtcz-build-console.txt")
    cmd = ["dotnet", "build"]
    if args.target:
        cmd.append(args.target)
    cmd += ["-v", "q", "-nologo", BUILD_PROPERTY]

    try:
        with open(console, "w", encoding="utf-8", errors="replace") as f:
            proc = subprocess.run(cmd, cwd=root, stdout=f,
                                  stderr=subprocess.STDOUT)
    except FileNotFoundError:
        out("build: dotnet not found on PATH - cannot build")
        return 4

    out(f"build-exit:{proc.returncode}")
    try:
        with open(console, encoding="utf-8", errors="replace") as f:
            for line in f.read().splitlines()[-8:]:
                out(line)
    except OSError:
        pass
    out(f"console: {console}")
    out()

    probe_rc = run_probe(root, args.pattern, args.max, args.warnings)

    if probe_rc == 1:
        return 1  # compiler errors — table printed, cause identified
    if proc.returncode != 0:
        # build failed yet SARIF is clean/absent: the failure never reached
        # the compiler (restore, SDK, bad project reference).
        out()
        out("GAP: build-exit nonzero but SARIF shows zero compiler errors - "
            "MSBuild-level failure (restore/SDK/project references); "
            "the informative line is in the console tail above.")
        return 3
    if probe_rc == 2:
        return 2  # build succeeded but produced no SARIF - flags not applied
    return 0


# ============================================================================
# exp — experience-routing lookup
# ============================================================================

AXIS_WEIGHT = {"tag": 3, "symptom": 2, "keyword": 1}


def strip_comment(line: str) -> str:
    """Remove a trailing ' #comment' unless the # falls inside quotes.
    Needed because the experiences skill's own template shows
    `tags: [a, b, c]   # 3-7 lowercase, hyphenated` - a real entry may carry
    that comment forward verbatim."""
    in_quote, quote_char = False, ""
    for i, ch in enumerate(line):
        if ch in ("\"", "'"):
            if not in_quote:
                in_quote, quote_char = True, ch
            elif ch == quote_char:
                in_quote = False
        elif ch == "#" and not in_quote and i > 0 and line[i - 1] in " \t":
            return line[:i].rstrip()
    return line


def parse_frontmatter(text: str):
    """Minimal `key: value` / `key: [list, of, values]` parser for the
    experiences frontmatter block. Returns None if no closed frontmatter
    block is found (unresolved over invented - callers treat None as
    malformed, never guess at partial data)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    closed = False
    for raw in lines[1:]:
        if raw.strip() == "---":
            closed = True
            break
        line = strip_comment(raw.strip())
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("\"'") for v in value[1:-1].split(",")]
            fields[key] = [v for v in items if v]
        else:
            fields[key] = value.strip("\"'")
    if not closed:
        return None
    return fields


def load_entries(root: str):
    """Returns (entries, malformed). entries: list of frontmatter dicts plus
    'path' (repo-relative, forward slashes, for citing/reading later).
    malformed: paths with no closed frontmatter block or no 'slug' field -
    surfaced, never silently dropped."""
    entries, malformed = [], []
    for path in sorted(glob.glob(os.path.join(root, "docs", "experiences", "*.md"))):
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            malformed.append(f"{path} (unreadable: {e})")
            continue
        fields = parse_frontmatter(text)
        if not fields or "slug" not in fields:
            malformed.append(path)
            continue
        fields["path"] = os.path.relpath(path, root).replace("\\", "/")
        entries.append(fields)
    return entries, malformed


def report_malformed(malformed) -> None:
    if not malformed:
        return
    out()
    out(f"Unparsable frontmatter (skipped, not counted): {len(malformed)}")
    for m in malformed[:10]:
        out(f"  - {m}")


def cmd_exp_inventory(args) -> int:
    entries, malformed = load_entries(args.root)
    if not entries and not malformed:
        out("Experience tag inventory: docs/experiences/ has no entries yet (0 files found).")
        return 2

    counts = Counter()
    for e in entries:
        for tag in e.get("tags", []):
            counts[tag] += 1

    out(f"Experience tag inventory - {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} scanned")
    out()
    out("| Count | Tag |")
    out("|---|---|")
    for tag, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        out(f"| {n} | {tag} |")
    report_malformed(malformed)
    return 0


def cmd_exp_search(args) -> int:
    entries, malformed = load_entries(args.root)
    if not entries and not malformed:
        out("Experience search: docs/experiences/ has no entries yet (0 files found).")
        return 2

    tags_wanted = [t.lower() for t in (args.tag or [])]
    symptom_wanted = args.symptom.lower() if args.symptom else None
    keywords_wanted = [k.lower() for k in (args.keyword or [])]

    if not (tags_wanted or symptom_wanted or keywords_wanted):
        out("Experience search: no --tag / --symptom / --keyword given - nothing to match against.")
        return 1

    hits = []
    for e in entries:
        matched_on = []
        entry_tags = [t.lower() for t in e.get("tags", [])]
        for t in tags_wanted:
            if any(t in et for et in entry_tags):
                matched_on.append(f"tag:{t}")
        if symptom_wanted and symptom_wanted in e.get("symptom", "").lower():
            matched_on.append("symptom")
        if keywords_wanted:
            try:
                with open(os.path.join(args.root, e["path"]), encoding="utf-8") as f:
                    body = f.read().lower()
            except OSError:
                body = ""
            for k in keywords_wanted:
                if k in body:
                    matched_on.append(f"keyword:{k}")
        if matched_on:
            score = sum(AXIS_WEIGHT[m.split(":")[0]] for m in matched_on)
            hits.append((score, e, matched_on))

    if not hits:
        out(f"Experience search: 0 candidates across {len(entries)} entries scanned.")
        report_malformed(malformed)
        return 0

    hits.sort(key=lambda h: (-h[0], h[1].get("slug", "")))
    total = len(hits)
    shown = hits[: args.max]

    out(f"Experience search: {total} candidate(s) across {len(entries)} entries scanned")
    out()
    out("| Slug | Matched On | Use-When | File |")
    out("|---|---|---|---|")
    for _, e, matched_on in shown:
        use_when = e.get("use-when", "[MISSING]")
        out(f"| {e.get('slug', '?')} | {', '.join(matched_on)} | {use_when} | {e['path']} |")
    out()
    if total > len(shown):
        out(f"Truncated: first {len(shown)} of {total} - narrow with more specific --tag/--symptom/--keyword for the rest")
    else:
        out("Truncated: none")
    report_malformed(malformed)
    return 0


# ============================================================================
# entry point
# ============================================================================

def _add_sarif_common(sp) -> None:
    sp.add_argument("--root", default=".", help="repo root; paths reported relative to it")
    sp.add_argument("--pattern", default="**/obj/**/msbuild.sarif",
                    help="glob for SARIF files under root")
    sp.add_argument("--max", type=int, default=30, help="max error rows in the table")
    sp.add_argument("--warnings", action="store_true", help="also print a warning table")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="amtcz",
        description="Standalone CLI for the AMaTsuCoZy SDLC kit. ASCII-only output.",
    )
    ap.add_argument("--version", action="version", version=f"amtcz {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # amtcz sarif {build,probe}
    sp_sarif = sub.add_parser("sarif", help="SARIF build diagnostics")
    sub_sarif = sp_sarif.add_subparsers(dest="sarif_cmd", required=True)

    sp_build = sub_sarif.add_parser(
        "build", help="clean stale logs, dotnet build with SARIF output, "
                      "extract report (exit 0/1/2/3/4)")
    sp_build.add_argument("target", nargs="?", default=None,
                          help=".sln/.csproj to build; omit to let dotnet pick")
    _add_sarif_common(sp_build)
    sp_build.set_defaults(func=cmd_sarif_build)

    sp_probe = sub_sarif.add_parser(
        "probe", help="extract report from SARIF logs already on disk, "
                      "no build (exit 0/1/2)")
    _add_sarif_common(sp_probe)
    sp_probe.set_defaults(func=cmd_sarif_probe)

    # amtcz exp {inventory,search}
    sp_exp = sub.add_parser("exp", help="experience-routing lookup "
                                        "(CLAUDE.md steps 1-2; exit 0/1/2)")
    sub_exp = sp_exp.add_subparsers(dest="exp_cmd", required=True)

    sp_inv = sub_exp.add_parser("inventory", help="tag frequency table (CLAUDE.md step 1)")
    sp_inv.add_argument("--root", default=".", help="repo root; docs/experiences/ is read relative to it")
    sp_inv.set_defaults(func=cmd_exp_inventory)

    sp_search = sub_exp.add_parser("search", help="find candidates + confirm trigger (CLAUDE.md step 2)")
    sp_search.add_argument("--root", default=".", help="repo root; docs/experiences/ is read relative to it")
    sp_search.add_argument("--tag", action="append", help="repeatable; substring match against an entry's tags")
    sp_search.add_argument("--symptom", help="substring match against the symptom: field")
    sp_search.add_argument("--keyword", action="append", help="repeatable; broad full-text fallback")
    sp_search.add_argument("--max", type=int, default=8, help="max rows in the candidate table")
    sp_search.set_defaults(func=cmd_exp_search)

    return ap


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except BrokenPipeError:
        # downstream pipe closed early (e.g. `amtcz ... | head`) - not an
        # error; silence the interpreter-exit flush complaint too.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())