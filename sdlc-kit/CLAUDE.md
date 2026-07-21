# Experience-First Task Routing (always applies)

Durable lessons live in `docs/experiences/*.md`. Before ANY investigation,
implementation, refactor, debugging, or technology decision, you MUST run this
routing — it is a required first step, not a suggestion:

1. Run the tag inventory first — unconditionally, every task, before
   deriving anything:
   `python3 ~/.claude/skills/experiences/scripts/experience_lookup.py inventory`
   Not gated on "if unsure" — self-assessed confidence is exactly what
   fails here; a tag you invented to fit the task sounds no less plausible
   to you than one actually grounded in the corpus, so that check never
   fires. Exit 2 (no entries yet) → skip straight to step 5, FRESH problem.
2. Derive 2–4 search terms from the task, matched against the tag list you
   just saw: technology names, error fragments, domain concepts. Prefer an
   inventory tag over a same-meaning invented one — inventory shows
   `dependency-injection`, not your first-instinct `di`; search on the
   former. This rule is about `--tag` specifically: `--symptom` and
   `--keyword` are free text and are not required to pre-exist in the
   inventory.
3. Find candidates and confirm their trigger in a single call — pass
   whichever of `--tag` / `--symptom` / `--keyword` fit, all combined in one
   invocation:
   `python3 ~/.claude/skills/experiences/scripts/experience_lookup.py search --tag <tag> --symptom "<error fragment>" --keyword "<broad term>"`
   About to type `--tag` without having run step 1 in this task? Stop, run
   step 1, then come back — that shortcut is the exact failure this
   routing exists to prevent.
   The report's Use-When column is the fit check: an entry is a match only
   if Use-When describes the situation you are in. A high match count or
   tag/keyword overlap alone is not a match; do not judge from filenames.
4. One or more confirmed → HISTORICAL problem: read the matching files (most
   specific first, others only if they bear on the same task) and apply their
   guidance BEFORE any new investigation or code changes.
5. None confirmed → FRESH problem: proceed with normal investigation. Do not
   force unrelated entries into context.
6. Scan the installed skill listing.
   Invoke EVERY skill whose description matches the current task — skills compose;
   loading one does not preclude another.
   A task may legitimately need source-navigator + dotnet-unit-testing together.
   Cite by name any skill you considered and deliberately skipped.
7. Any decision that relies on an entry — or deliberately overrides one — must
   cite it by slug.
8. If a fresh problem's solution is likely to help again in this repository,
   invoke the `experiences` skill to capture it before closing the task.
9. Subagents do NOT inherit this routing — their context starts empty. When
   spawning a subagent of any kind, attach the confirmed-relevant entries'
   Lesson and Applies When/Not When sections (with slugs) directly in the
   dispatch prompt. Attach only confirmed matches, never unconfirmed
   candidates.