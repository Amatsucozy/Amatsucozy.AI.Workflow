#!/usr/bin/env python3
"""Retrieve docs/experiences/*.md entries for the CLAUDE.md experience-routing
protocol. Replaces the grep/sed/tr/sort pipeline so retrieval behaves the
same regardless of shell (bash, zsh, PowerShell, none at all) — the prior
pipeline depended on GNU-flavored sed/tr/sort semantics that don't hold on
every environment this kit runs in.

Pairs with CLAUDE.md steps 1-2:
    step 1 (tag inventory, only when vocabulary is unknown):
        python3 .claude/skills/experiences/scripts/experience_lookup.py inventory
    step 2 (find candidates + confirm trigger, in one call):
        python3 .claude/skills/experiences/scripts/experience_lookup.py search \
            --tag ef-core --tag dependency-injection \
            --symptom "second interface resolves a different instance" \
            --keyword "scoped lifetime"

Reads frontmatter only (never full lesson bodies) for tag/symptom matching —
the routing decision is made from ~10 lines/entry. --keyword additionally
scans full file text, matching the old `grep -li` fallback. Full reads happen
only after a candidate is confirmed (CLAUDE.md step 3) — this script never
prints Lesson/Evidence/Applies-When bodies.

Stdlib only. Exit codes: 0 = ran (0 hits is a valid outcome), 1 = usage
error (no search flags given), 2 = docs/experiences/ has no entries yet.
"""

import argparse
import glob
import os
import sys
from collections import Counter

AXIS_WEIGHT = {"tag": 3, "symptom": 2, "keyword": 1}


def strip_comment(line: str) -> str:
    """Remove a trailing ' #comment' unless the # falls inside quotes.
    Needed because the experiences skill's own template shows
    `tags: [a, b, c]   # 3-7 lowercase, hyphenated` — a real entry may carry
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
    block is found (unresolved over invented — callers treat None as
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
    malformed: paths with no closed frontmatter block or no 'slug' field —
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
    print()
    print(f"Unparsable frontmatter (skipped, not counted): {len(malformed)}")
    for m in malformed[:10]:
        print(f"  - {m}")


def cmd_inventory(args) -> int:
    entries, malformed = load_entries(args.root)
    if not entries and not malformed:
        print("Experience tag inventory: docs/experiences/ has no entries yet (0 files found).")
        return 2

    counts = Counter()
    for e in entries:
        for tag in e.get("tags", []):
            counts[tag] += 1

    print(f"Experience tag inventory - {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} scanned")
    print()
    print("| Count | Tag |")
    print("|---|---|")
    for tag, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"| {n} | {tag} |")
    report_malformed(malformed)
    return 0


def cmd_search(args) -> int:
    entries, malformed = load_entries(args.root)
    if not entries and not malformed:
        print("Experience search: docs/experiences/ has no entries yet (0 files found).")
        return 2

    tags_wanted = [t.lower() for t in (args.tag or [])]
    symptom_wanted = args.symptom.lower() if args.symptom else None
    keywords_wanted = [k.lower() for k in (args.keyword or [])]

    if not (tags_wanted or symptom_wanted or keywords_wanted):
        print("Experience search: no --tag / --symptom / --keyword given - nothing to match against.")
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
        print(f"Experience search: 0 candidates across {len(entries)} entries scanned.")
        report_malformed(malformed)
        return 0

    hits.sort(key=lambda h: (-h[0], h[1].get("slug", "")))
    total = len(hits)
    shown = hits[: args.max]

    print(f"Experience search: {total} candidate(s) across {len(entries)} entries scanned")
    print()
    print("| Slug | Matched On | Use-When | File |")
    print("|---|---|---|---|")
    for _, e, matched_on in shown:
        use_when = e.get("use-when", "[MISSING]")
        print(f"| {e.get('slug', '?')} | {', '.join(matched_on)} | {use_when} | {e['path']} |")
    print()
    if total > len(shown):
        print(f"Truncated: first {len(shown)} of {total} - narrow with more specific --tag/--symptom/--keyword for the rest")
    else:
        print("Truncated: none")
    report_malformed(malformed)
    return 0


def main() -> int:
    # Force UTF-8 stdout with graceful fallback instead of the platform
    # default (e.g. cp1252/cp437 on Windows), which can silently drop or
    # garble non-ASCII output on legacy console codepages.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root; docs/experiences/ is read relative to it")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_inv = sub.add_parser("inventory", help="tag frequency table (CLAUDE.md step 1)")
    sp_inv.set_defaults(func=cmd_inventory)

    sp_search = sub.add_parser("search", help="find candidates + confirm trigger (CLAUDE.md step 2)")
    sp_search.add_argument("--tag", action="append", help="repeatable; substring match against an entry's tags")
    sp_search.add_argument("--symptom", help="substring match against the symptom: field")
    sp_search.add_argument("--keyword", action="append", help="repeatable; broad full-text fallback")
    sp_search.add_argument("--max", type=int, default=8, help="max rows in the candidate table")
    sp_search.set_defaults(func=cmd_search)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
