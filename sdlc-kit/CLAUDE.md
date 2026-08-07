# Experience-First Task Routing (always applies)

Durable lessons live in `docs/experiences/*.md`. Before ANY investigation,
implementation, refactor, debugging, or technology decision, you MUST run this
routing — it is a required step, not a suggestion. It runs once you know what
you're solving, never before: don't fire the inventory on a bare greeting or
an unparsed human message, and don't fire it while you're still mid-intake
clarifying scope. The "unconditional" language in step 2 is about not
skipping the search once a task exists — it is not license to run tooling
before one does.

1. State the problem in one sentence before touching any tooling. Read (or,
   if intake is incomplete, ask for) what you're actually trying to solve —
   the symptom, the feature, the question. If you can't state it yet, you're
   not ready for step 2; get it from the human or the ticket first.
2. Run the tag inventory — unconditionally, every task, once step 1 is
   satisfied, before deriving anything else:
   `amtcz exp inventory`
   Not gated on "if unsure" — self-assessed confidence is exactly what
   fails here; a tag you invented to fit the task sounds no less plausible
   to you than one actually grounded in the corpus, so that check never
   fires. Exit 2 (no entries yet) → skip straight to step 6, FRESH problem.
3. Derive 2–4 search terms from the task, matched against the tag list you
   just saw: technology names, error fragments, domain concepts. Prefer an
   inventory tag over a same-meaning invented one — inventory shows
   `dependency-injection`, not your first-instinct `di`; search on the
   former. This rule is about `--tag` specifically: `--symptom` and
   `--keyword` are free text and are not required to pre-exist in the
   inventory.
4. Find candidates and confirm their trigger in a single call — pass
   whichever of `--tag` / `--symptom` / `--keyword` fit, all combined in one
   invocation:
   `amtcz exp search --tag <tag> --symptom "<error fragment>" --keyword "<broad term>"`
   About to type `--tag` without having run step 2 in this task? Stop, run
   step 2, then come back — that shortcut is the exact failure this
   routing exists to prevent.
   The report's Use-When column is the fit check: an entry is a match only
   if Use-When describes the situation you are in. A high match count or
   tag/keyword overlap alone is not a match; do not judge from filenames.
5. One or more confirmed → HISTORICAL problem: read the matching files (most
   specific first, others only if they bear on the same task) and apply their
   guidance BEFORE any new investigation or code changes.
6. None confirmed → FRESH problem: proceed with normal investigation. Do not
   force unrelated entries into context.
7. Scan the installed skill listing.
   Invoke EVERY skill whose description matches the current task — skills compose;
   loading one does not preclude another.
   A task may legitimately need source-navigator + dotnet-unit-testing together.
   Cite by name any skill you considered and deliberately skipped.
8. Any decision that relies on an entry — or deliberately overrides one — must
   cite it by slug.
9. If a fresh problem's solution is likely to help again in this repository,
   invoke the `experiences` skill to capture it before closing the task.
10. Subagents do NOT inherit this routing — their context starts empty. When
   spawning a subagent of any kind, attach the confirmed-relevant entries'
   Lesson and Applies When/Not When sections (with slugs) directly in the
   dispatch prompt. Attach only confirmed matches, never unconfirmed
   candidates. `amtcz` is on the machine PATH, so it resolves for subagent
   Bash calls too; a subagent that finds it absent reports `blocked` — the
   degraded-mode decision belongs to the human via the main thread, never
   to a subagent.

---

## Reference

`amtcz` is guaranteed installed — no fallback branch, no probe-and-STOP gate.
The commands this file calls (`exp inventory`, `exp search`) are given above
in full; `run-build`/`run-test` likewise inline the one command each calls.
For anything beyond those — uncommon flags, `--rebuild`, `exp` search
scoring, a rejected flag, or troubleshooting — invoke the `amtcz-cli` skill.
Not inlined here to keep this always-on file cheap; the skill's own
description covers when to reach for it, so step 7's skill scan surfaces it
on its own for tasks this file doesn't anticipate.