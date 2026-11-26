# Claude SDLC Project Instructions

Resolve `docs/experiences/` and `docs/tasks/` relative to the target project root.

## Working Conventions

- User instructions and existing authorization take precedence over these
  conventions. Continue authorized work; ask only for material missing
  information or an action that still needs approval.
- Load skills whose workflow fits the request. An ordinary edit or question
  does not start the SDLC pipeline just because it uses tools.
- End-to-end pipeline work runs under
  [sdlc-orchestrator](skills/sdlc-orchestrator/SKILL.md), which pulls in
  [requirements](skills/requirements/SKILL.md),
  [planning](skills/planning/SKILL.md), and
  [reporting](skills/reporting/SKILL.md) at their stages. Task state lives in
  `docs/tasks/<id>/main.yaml`.
- Subagents (`.claude/agents/`) are dispatched only when the user or the
  active workflow calls for them. A subagent sees none of your conversation,
  searches, or reads, so pass its inputs explicitly — inputs, not method; the
  agent file owns its tools and workflow.
- Batch independent reads and searches in one message; keep dependent
  operations and edits sequential.
- When a tool's project root differs from the shell working directory, pass
  the right `root` or path instead of assuming `.`.

## MCP Servers

Each server documents its own tools and verdicts; follow that guidance.
Prefixes vary by registration, so match the server and operation, then read
the actual schema.

| Server | Use for |
|---|---|
| `amtcz` | .NET build (`sarif_build`), tests (`test_run`), experience search (`exp_*`) |
| `dbschema` | Database structure lookup — never rows; you write the SQL |
| `roslyn` | C# semantics: positions, callers, implementers, per-file diagnostics |

- Builds and tests go through [run-build](skills/run-build/SKILL.md) and
  [run-test](skills/run-test/SKILL.md). In the pipeline they belong to
  reviewer gates unless the user asks for a main-thread run.
- Raw build/test logs never enter context; the structured report is the
  output. If a required tool is missing, report the check as blocked rather
  than substituting raw `dotnet` commands.
- For a concept-level question in a multi-project repo, read the repo
  `CLAUDE.md`'s `## Project Map` (if any) to pick the project, find the file
  with Glob/Grep, then use roslyn for positions, callers, and implementers.

## Experience-First Routing

Durable lessons live in `docs/experiences/*.md`. Route once the problem is
defined and before investigation, implementation, debugging, or a technology
decision; route again when a new failure brings different symptoms.

1. State the problem in one sentence and name its concerns: `implementation`
   always, plus `tests` when the work adds, changes, or fixes tests. Route
   each concern separately — test lessons are tagged by framework, fixture,
   and assertion vocabulary that an implementation problem statement never
   produces.
2. Call `exp_inventory` first and take tags from it rather than inventing
   synonyms. `no_entries` means nothing to search.
3. Call `exp_search` once per concern with 2–4 terms (tags, error fragments,
   domain words; for `tests`, the framework, mocking/assertion libraries, and
   fixture patterns). A candidate matches only if its Use-When describes your
   situation — for `tests`, writing or fixing the tests.
4. Read confirmed matches and apply them before new work. Cite the slug when
   relying on or overriding a lesson. Declare the outcome per concern:
   matched slugs, or "no experience match (<concern>)".
5. When delegating, attach the confirmed entries' Lesson and Applies When/Not
   When sections, with slugs, matched to the delegate's concern. Never attach
   unconfirmed candidates.
6. At close, use [experiences](skills/experiences/SKILL.md) if an
   evidence-backed finding would help future work.

Without the experience tools, Grep the entries' `tags:`, `symptom:`, and
`use-when:` fields and read candidates to confirm. A missing directory means
no match; an unreadable one is an access gap to report, not proof of absence.
A subagent that lacks a required capability reports `blocked` rather than
claiming the check ran.
