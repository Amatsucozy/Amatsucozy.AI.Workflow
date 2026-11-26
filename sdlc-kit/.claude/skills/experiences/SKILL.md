---
name: experiences
description: Write or update a durable lesson under docs/experiences/. Use at task close, after a costly failure or surprising discovery, when evidence validates or invalidates a design choice, or when the human says "remember this" / "write this down". Writing only — reading is ambient via the CLAUDE.md experience routing.
---

# Experience Memory — Writer

One markdown file per lesson. The frontmatter is the retrieval index
(`exp_search` and grep read it), so its quality decides whether the entry is
ever found again.

## When to Write

- A failure cost more than ~30 minutes and had a generalizable cause.
- Evidence (gate results count) validated or invalidated a design choice.
- A surprising behavior of a library, tool, or this codebase was confirmed.

Skip one-off typos, restatements of official docs, and anything an existing
entry covers. Ten sharp entries beat a hundred journal notes.

Before writing, run `exp_search` with the lesson's own tags, symptom, and
keywords — the routing at task start searched for the task, not this finding.
A hit whose Use-When covers the finding is updated in place (Evidence,
confidence, source-task), not duplicated.

## Format — `docs/experiences/<slug>.md`

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
<2–3 sentences of context.>

## Lesson
<The transferable rule, actionable without the Situation. One paragraph max.>

## Evidence
<What failed, what fixed it, measurements; file:line or commit refs.>

## Applies When / Not When
<Boundary of validity — the guard against over-applying the lesson.>
```

- `use-when` is the primary discovery surface: describe the situation a
  future task would be in, not a topic label.
- `symptom` is the phrase you'd grep when hitting the problem cold — an error
  fragment or observed misbehavior.
- `tags`: reuse tags from `exp_inventory`; a synonym splits the corpus.
- Test lessons are found by the `tests` concern, which searches by framework,
  mocking/assertion libraries, and fixture patterns — tag and phrase them that
  way (`xunit`, `mocking`, `test-fixtures`; "use when writing xunit tests for
  a scoped EF Core service"), not only by the production type under test.

## Lifecycle

- `observed-once` → `proven` when a second task confirms it (add its
  source-task to Evidence).
- Correct contradicted entries in place with a one-line note of what changed;
  don't delete them — the correction is itself a lesson.
