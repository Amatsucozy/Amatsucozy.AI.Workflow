---
name: amtcz-cli
description: >
  Full command reference for the `amtcz` CLI — sarif build/probe, test
  run/probe, exp inventory/search — covering every flag, exit code, and
  troubleshooting note beyond what run-build, run-test, and CLAUDE.md's
  experience routing already inline. Use this whenever an amtcz call needs
  a flag those three don't show (--rebuild, --pattern, --warnings, exp
  search's --tag/--symptom/--keyword scoring), whenever an amtcz call
  returns an exit code or rejects a flag unexpectedly, whenever the human
  asks how amtcz works or wants to run it directly outside the pipeline, or
  whenever authoring or editing a skill/script that shells out to amtcz. Do
  NOT use for the routine sarif-build-at-a-gate or test-run-at-a-gate calls
  (run-build / run-test already own those) or for the exp inventory/search
  sequence itself (CLAUDE.md governs that) — this skill is for everything
  past what those three already carry.
---

# Skill: amtcz-cli

`amtcz` is guaranteed installed on PATH — no fallback branch, no degraded
mode, no probe-and-STOP gate anywhere in this kit. This skill is the
reference for using it directly, beyond the one command each of
`run-build`, `run-test`, and CLAUDE.md's experience routing already inlines.

## When to Use

- An amtcz call needs a flag not already shown by `run-build`/`run-test`
  (`--rebuild`, `--pattern`, `--warnings`, `exp search`'s scoring across
  `--tag`/`--symptom`/`--keyword`).
- An amtcz call returns an exit code you don't recognize, or a documented
  flag gets rejected — check `amtcz --version` first; a rejection usually
  means the installed CLI predates this doc (see amtcz-cli/README.md
  Install/Upgrade).
- The human asks how amtcz works, wants to run it directly outside the
  pipeline, or is troubleshooting its output.
- You're authoring or editing a skill or script that shells out to `amtcz`.

**Not for:** the routine `sarif build` call at a build gate (→ `run-build`),
the routine `test run` call at a verification gate (→ `run-test`), or the
experience inventory/search sequence (→ CLAUDE.md steps 2–4). Those three
already carry the exact command each of them calls; reach for this skill
only past that point.

## Quick Reference

| Command | Does |
|---|---|
| `amtcz sarif build [target]` | incremental-safe SARIF build + deduped error table |
| `amtcz sarif probe` | re-extract from SARIF logs already on disk, no rebuild |
| `amtcz test run [target]` | TRX-logged test run + failure-only table |
| `amtcz test probe` | re-extract from TRX already on disk, no rerun |
| `amtcz exp inventory` | tag frequency table over experience frontmatter |
| `amtcz exp search` | candidate lessons + Use-When confirmation column |

Full flags, exit-code tables, and shared behavior (ASCII-only output,
exit-codes-are-the-verdict, temp-file console redirection): see
`references/amtcz-manual.md`.

## Hard Rules

- Never `cat` a console temp file, a `.trx`, or a `.sarif` directly — the
  extracted table is the only permitted path into context.
- Exit codes are the verdict. Never re-derive pass/fail by parsing stdout.
- No fallback branch exists anywhere in this kit. If `amtcz` is missing
  from PATH, stop and tell the human directly — an environment problem, not
  something to work around.