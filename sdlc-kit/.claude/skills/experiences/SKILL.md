---
name: experiences
description: Write or update a durable lesson under docs/experiences/. Use at task close, after a costly failure or surprising discovery, when evidence validates or invalidates a design choice, or when the human says "remember this" / "write this down". Writing only — reading is ambient via the CLAUDE.md experience routing.
---

# Experience Memory — Writer

One markdown file per lesson. The frontmatter IS the retrieval index
(`exp_search` and grep read it), so its quality decides whether the entry is
ever found again.

## Before Writing

Run `exp_search` with the lesson's own tags, symptom, and keywords — the
routing at task start searched for the *task*, not for this finding. A hit
whose Use-When covers the finding is updated in place (Evidence, confidence,
source-task), never duplicated.

## When to Write

Write when any of these hold:
- A failure cost more than ~30 minutes and had a generalizable cause.
- A design choice was validated or invalidated by evidence (gate results count).
- A surprising behavior of a library, tool, or this codebase was confirmed.

Do NOT write for one-off typos, restatements of official docs, or anything an
existing entry covers. Ten sharp entries beat a hundred journal notes.

## File Format — `docs/experiences/<slug>.md`

```markdown
---
slug: efcore-scoped-di-multi-interface
use-when: "use when registering one implementation under multiple interfaces with scoped lifetime"
domain: dotnet | claude-code | infra | process | <area>
tags: [ef-core, dependency-injection, scoped-lifetime]   # 3–7 lowercase, hyphenated
symptom: "second interface resolves a different instance"
confidence: proven | observed-once
date: YYYY-MM-DD
source-task: <ticket id>
---

# <Title stating the lesson, not the topic>

## Situation
<2–3 sentences: the context in which this arose.>

## Lesson
<The transferable rule, actionable without re-reading Situation. One strong
paragraph max — this is the payload.>

## Evidence
<What failed, what fixed it, measurement if any; file:line or commit refs.>

## Applies When / Not When
<Boundary of validity — the guard against over-applying the lesson.>
```

Quality bars:
- `use-when`: a concrete "use when ..." trigger sentence — the PRIMARY
  discovery surface (routing confirms candidates against it). Write the
  situation a future task would be in, not a topic label.
- `symptom`: the exact phrase future-you would grep when hitting the problem
  cold — an error-message fragment or observed misbehavior, not a summary.
- `tags`: reuse tags already in `exp_inventory` before coining new ones — a
  synonym tag splits the corpus and hides the entry from routing.

## Lifecycle

- `observed-once` → `proven` when a second task confirms it (append the second
  source-task to Evidence).
- Contradicted entries are corrected in place with a one-line note of what
  changed — never silently deleted; the correction is itself a lesson.
