"""Experience-memory lookup (docs/experiences/*.md) — pure extraction.

Vendored from amtcz-cli/amtcz.py (exp section). No code sharing with
amtcz-cli: this is an independent copy, adapted to return dataclasses
instead of printing tables.
"""

from __future__ import annotations

import glob
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

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


@dataclass
class ExpEntry:
    slug: str
    use_when: str
    domain: str
    tags: list[str]
    symptom: str
    confidence: str
    date: str
    source_task: str
    path: str


def _to_entries(raw: list[dict]) -> list[ExpEntry]:
    """Maps a load_entries() frontmatter dict (hyphenated keys, as they
    appear in the markdown frontmatter itself) to an ExpEntry (underscored
    field names)."""
    return [
        ExpEntry(
            slug=e.get("slug", ""),
            use_when=e.get("use-when", "[MISSING]"),
            domain=e.get("domain", ""),
            tags=e.get("tags", []) or [],
            symptom=e.get("symptom", ""),
            confidence=e.get("confidence", ""),
            date=e.get("date", ""),
            source_task=e.get("source-task", ""),
            path=e.get("path", ""),
        )
        for e in raw
    ]


@dataclass
class ExpInventoryResult:
    verdict: Literal["no_entries", "ok"]
    entry_count: int = 0
    tag_counts: dict[str, int] = field(default_factory=dict)
    malformed: list[str] = field(default_factory=list)


def inventory(root: str) -> ExpInventoryResult:
    """Replaces cmd_exp_inventory(). Verdict: no_entries when zero entries
    AND zero malformed (old exit 2); else ok, with tag_counts built the same
    way (Counter over each entry's tags)."""
    raw, malformed = load_entries(root)
    if not raw and not malformed:
        return ExpInventoryResult(verdict="no_entries", entry_count=0,
                                   tag_counts={}, malformed=malformed)

    entries = _to_entries(raw)
    counts: Counter = Counter()
    for e in entries:
        for tag in e.tags:
            counts[tag] += 1
    tag_counts = {tag: n for tag, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))}

    return ExpInventoryResult(verdict="ok", entry_count=len(entries),
                               tag_counts=tag_counts, malformed=malformed)


@dataclass
class ExpSearchHit:
    slug: str
    matched_on: list[str]
    use_when: str
    path: str
    score: int


@dataclass
class ExpSearchResult:
    verdict: Literal["no_entries", "usage_error", "ok"]
    total_hits: int = 0
    hits: list[ExpSearchHit] = field(default_factory=list)
    truncated: bool = False
    malformed: list[str] = field(default_factory=list)


def search(root: str, tags: list[str] | None, symptom: str | None,
           keywords: list[str] | None, max_rows: int) -> ExpSearchResult:
    """Replaces cmd_exp_search(). Verdict: no_entries gate first (old exit
    2); usage_error when none of tags/symptom/keywords given (old exit 1);
    else score/match entries exactly as the original, sort by
    (-score, slug), verdict ok. total_hits reflects ALL hits; hits holds
    only the top max_rows; truncated = total_hits > len(hits)."""
    raw, malformed = load_entries(root)
    if not raw and not malformed:
        return ExpSearchResult(verdict="no_entries", total_hits=0, hits=[],
                                truncated=False, malformed=malformed)

    tags_wanted = [t.lower() for t in (tags or [])]
    symptom_wanted = symptom.lower() if symptom else None
    keywords_wanted = [k.lower() for k in (keywords or [])]

    if not (tags_wanted or symptom_wanted or keywords_wanted):
        return ExpSearchResult(verdict="usage_error", total_hits=0, hits=[],
                                truncated=False, malformed=malformed)

    entries = _to_entries(raw)

    scored: list[tuple[int, ExpEntry, list[str]]] = []
    for e in entries:
        matched_on: list[str] = []
        entry_tags = [t.lower() for t in e.tags]
        for t in tags_wanted:
            if any(t in et for et in entry_tags):
                matched_on.append(f"tag:{t}")
        if symptom_wanted and symptom_wanted in e.symptom.lower():
            matched_on.append("symptom")
        if keywords_wanted:
            try:
                with open(os.path.join(root, e.path), encoding="utf-8") as f:
                    body = f.read().lower()
            except OSError:
                body = ""
            for k in keywords_wanted:
                if k in body:
                    matched_on.append(f"keyword:{k}")
        if matched_on:
            score = sum(AXIS_WEIGHT[m.split(":")[0]] for m in matched_on)
            scored.append((score, e, matched_on))

    if not scored:
        return ExpSearchResult(verdict="ok", total_hits=0, hits=[],
                                truncated=False, malformed=malformed)

    scored.sort(key=lambda h: (-h[0], h[1].slug))
    total_hits = len(scored)
    shown = scored[:max_rows]

    hits = [
        ExpSearchHit(slug=e.slug, matched_on=matched_on, use_when=e.use_when,
                      path=e.path, score=score)
        for score, e, matched_on in shown
    ]

    return ExpSearchResult(
        verdict="ok",
        total_hits=total_hits,
        hits=hits,
        truncated=total_hits > len(hits),
        malformed=malformed,
    )
