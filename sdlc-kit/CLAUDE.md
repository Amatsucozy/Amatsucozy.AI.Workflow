# Experience-First Task Routing (always applies)

Durable lessons live in `docs/experiences/*.md`. Before ANY investigation,
implementation, refactor, debugging, or technology decision, you MUST run this
routing — it is a required first step, not a suggestion:

1. Derive 2–4 search terms from the task: technology names, error fragments,
   domain concepts. If unsure what vocabulary entries use, list the tag
   inventory first:
   `grep -h '^tags:' docs/experiences/*.md | tr -d '[]' | sed 's/^tags: *//' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort | uniq -c | sort -rn`
2. Find candidates by semantic relevance (run what fits, batched):
   `grep -l "tags:.*<tag>" docs/experiences/*.md`                    (by tag)
   `grep -li "symptom:.*<error fragment>" docs/experiences/*.md`     (for errors)
   `grep -li "<keyword>" docs/experiences/*.md | head -5`            (broad)
3. Confirm fit — check ONLY the candidates' triggers:
   `grep -H '^use-when:' <candidate files>`
   An entry is a match only if its `use-when` describes the situation you are
   in. Tag overlap alone is not a match; do not judge from filenames.
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
