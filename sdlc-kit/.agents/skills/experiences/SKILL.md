---
name: experiences
description: Create or update durable lessons in docs/experiences when the user asks to remember a finding, or a completed task yields a reusable, evidence-backed lesson. Search existing entries before writing; do not create entries for routine fixes.
---

# Experience Memory — Writer

One markdown file per lesson. The frontmatter IS the retrieval index (readers
grep it), so its quality determines whether the entry is ever found again.

## Before Writing

Search existing `docs/experiences/` entries by tags, symptom, and `use-when`
using the available experience tools or `rg`. Read matching entries and update
an existing lesson when it already covers the finding. Follow any project
experience read protocol in AGENTS.md; this writer does not require that file.

## When to Write

Write when any of these hold:
- A failure cost more than ~30 minutes and had a generalizable cause.
- A design choice was validated or invalidated by evidence (gate results count).
- A surprising behavior of a library, tool, or this codebase was confirmed.

Do NOT write for: one-off typos, restatements of official docs, or anything an
existing entry covers — update that entry's Evidence/confidence instead. Ten
sharp entries beat a hundred journal notes.

## File Format — `docs/experiences/<slug>.md`

```markdown
---
slug: efcore-scoped-di-multi-interface
use-when: "use when registering one implementation under multiple interfaces with scoped lifetime"
domain: dotnet | codex | infra | process | <area>
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

Quality bar for `use-when`: a concrete "use when..." trigger sentence — it is
the PRIMARY discovery surface for experience searches,
so write it as the situation a future task would be in, not as a topic label.

Quality bar for `symptom`: the exact phrase future-you would grep when hitting
the problem cold — an error-message fragment or observed misbehavior, not an
abstract summary.

Quality bar for test lessons: the routing's `tests` concern finds them by
test framework, mocking/assertion libraries, and fixture or naming patterns —
tag and phrase `use-when` that way (`xunit`, `mocking`, `test-fixtures`; "use
when writing xunit tests for a scoped EF Core service"), not only by the
production type under test.

## Lifecycle

- `observed-once` → `proven` when a second task confirms it (append the second
  source-task to Evidence).
- Contradicted entries are corrected in place with a one-line note of what
  changed — never silently deleted; the correction is itself a lesson.