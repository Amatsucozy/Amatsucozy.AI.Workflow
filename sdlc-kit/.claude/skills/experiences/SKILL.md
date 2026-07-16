---
name: experiences
description: Create and maintain experience memory entries under docs/experiences/ — durable lessons learned. Invoke at task close, after any notable failure or surprising discovery, when a design choice gets validated or invalidated by evidence, or when the human says "remember this", "we've hit this before", or "write this down". Writing only — reading/searching entries is ambient (see CLAUDE.md read protocol) and needs no skill.
---

# Experience Memory — Writer

One markdown file per lesson. The frontmatter IS the retrieval index (readers
grep it), so its quality determines whether the entry is ever found again.

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

Quality bar for `use-when`: a concrete "use when..." trigger sentence — it is
the PRIMARY discovery surface (CLAUDE.md routes tasks by matching against it),
so write it as the situation a future task would be in, not as a topic label.

Quality bar for `symptom`: the exact phrase future-you would grep when hitting
the problem cold — an error-message fragment or observed misbehavior, not an
abstract summary.

## Lifecycle

- `observed-once` → `proven` when a second task confirms it (append the second
  source-task to Evidence).
- Contradicted entries are corrected in place with a one-line note of what
  changed — never silently deleted; the correction is itself a lesson.