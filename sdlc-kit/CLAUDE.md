# Tooling Resolution (used by any step that invokes kit tooling)

All scripted tooling ships as ONE artifact: the standalone `amtcz` CLI
(gh/az-style), installed machine-level onto PATH via pipx or pip. There are
no per-skill scripts; the CLI is the single source of truth, and the same
binary serves Claude Code sessions, subagents, bare CI, and manual shells.

**Probe once per session, before the first tooling invocation:**

```bash
command -v amtcz >/dev/null 2>&1 && amtcz --version
```

**If present:** use `amtcz <subcommand>` for every invocation this session.
The echoed version is the skew guard — if a documented flag is rejected, the
installed CLI is older than the docs; surface that, don't work around it.

**If absent: STOP.** Do not improvise a substitute, do not silently degrade.
Report to the human, verbatim options included:

> The `amtcz` CLI is not on PATH. Choose:
> (a) install it — `pipx install <amtcz-cli path or git url>` (or
>     `pip install --user`, `py -m pip install --user` on Windows) — and I
>     wait; or
> (b) approve DEGRADED MODE for this session: I use the documented verbatim
>     commands below — lossy (no dedupe, no cascade verdict, no match
>     scoring) but runnable.

Then wait. Degraded mode requires explicit approval, is scoped to the
current session only, and is noted in every turn report while active
(`tooling: degraded`). No approval → no tooling-dependent step runs.

**Degraded verbatim commands** (run exactly these — improvised variants are
the failure this section exists to prevent):

| Replaces | Degraded command |
|---|---|
| `amtcz sarif build <target>` | `dotnet build <target> -v q -nologo > /tmp/build-console.txt 2>&1; echo "build-exit:$?"; tail -8 /tmp/build-console.txt; grep -E ": (error\|warning) [A-Z]+[0-9]+" /tmp/build-console.txt \| sort -u \| head -30` (console text — expect duplicates; gap rule = compare build-exit against grep hits by hand) |
| `amtcz sarif probe` | re-read `/tmp/build-console.txt` via the same grep — no rebuild |
| `amtcz exp inventory` | `grep -h "^tags:" docs/experiences/*.md` (read the raw tag lines; no frequency table) |
| `amtcz exp search` | `grep -il "<term>" docs/experiences/*.md` per term, then `grep -H "^use-when:\|^symptom:" <hits>` — confirm via Use-When exactly as in step 3 below |

# Experience-First Task Routing (always applies)

Durable lessons live in `docs/experiences/*.md`. Before ANY investigation,
implementation, refactor, debugging, or technology decision, you MUST run this
routing — it is a required first step, not a suggestion:

1. Run the tag inventory first — unconditionally, every task, before
   deriving anything:
   `amtcz exp inventory`
   (CLI absent → the Tooling Resolution gate above fires FIRST; this step
   does not run until the human has chosen.)
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
   `amtcz exp search --tag <tag> --symptom "<error fragment>" --keyword "<broad term>"`
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
   candidates. `amtcz` is on the machine PATH, so it resolves for subagent
   Bash calls too; a subagent that finds it absent reports `blocked` — the
   degraded-mode decision belongs to the human via the main thread, never
   to a subagent.