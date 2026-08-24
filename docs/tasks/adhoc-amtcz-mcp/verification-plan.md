## Gate Schedule

| Gate | After | Build | Tests | Est. cost |
|---|---|---|---|---|
| G1 | Phase 3 | `docker build` (best-effort) | full `pytest` suite + tool-registration check | ~3 min |
| G2 (final) | Phase 4 | `docker build` (best-effort, re-check) | full `pytest` suite (regression) + doc-consistency checks + full AC audit | ~3 min |

Deviation from the kit's default pipeline, flagged for approval: these gates
run `pytest` directly via Bash rather than through the `run-build`/`run-test`
skills, because those skills are .NET/SARIF/TRX-specific and don't apply to
testing this Python package. Output stays capped (pytest's own `-q` summary
plus failure lines only), preserving the Hard Rule's intent even though the
mechanism differs.

## Zero-Cost Checks (any time, no build)

- `git diff --name-only` vs. each phase's declared Scope — anything unlisted
  is scope-drift.
- `python -m py_compile` on every new `.py` file — catches syntax errors
  before pytest.
- No secrets/credentials in the diff (`git diff` skim).
- `git diff -- amtcz-cli/amtcz.py` is empty at every point after Phase 1
  (confirms the "no dependency, no edits" decision held).

## Gate G1 (after Phase 3)

| Check | Command | Pass condition | On fail |
|---|---|---|---|
| Package installs | `pip install -e "amtcz-mcp[dev]"` | exits 0 | fix-phase on `pyproject.toml` |
| Full test suite | `cd amtcz-mcp && pytest -q` | all tests pass, 0 failures/errors | fix-phase scoped to the failing module (sarif/trx/experiences/server) |
| Tool registration | `python -c "from amtcz_mcp.server import mcp; print(sorted(t.name for t in mcp._tool_manager.list_tools()))"` (adjust to the actual FastMCP introspection API found during implementation) | prints exactly `['exp_inventory','exp_search','sarif_build','sarif_probe','test_probe','test_run']` | fix-phase on `server.py` registration |
| Docker build (best-effort) | `docker build -t amtcz-mcp amtcz-mcp/` | succeeds, OR Docker/daemon unavailable in this environment (note and continue — not a gate failure) | if Docker is available and the build fails, fix-phase on `Dockerfile`; if unavailable, note in the turn report and rely on manual verification before real-world use |

## Gate G2 (final, after Phase 4)

| Check | Command | Pass condition | On fail |
|---|---|---|---|
| Regression: test suite | `cd amtcz-mcp && pytest -q` | still all-green | fix-phase |
| Regression: amtcz-cli untouched | `git diff --stat -- amtcz-cli/` | empty except `amtcz-cli/README.md` (Phase 4.5's deprecation note) | fix-phase reverting stray edits |
| AC-1 (6 tools, self-describing) | inspect `server.py` docstrings for the 6 tools (manual read) | each has a docstring covering purpose, params, verdict meanings | fix-phase |
| AC-2 (structured verdicts) | pytest suite (already run above) + manual read of one `SarifReport`/`TrxReport`/`ExpSearchResult` dataclass definition against research's exit-code table | every distinct exit code from research maps to a distinct `verdict` value, 1:1, for each of the 6 ops | fix-phase |
| AC-3 (Docker + README) | `ls amtcz-mcp/Dockerfile amtcz-mcp/README.md`; docker build check from G1 | both files exist; README documents build+run+register+tool list | fix-phase |
| AC-4 (docs migrated) | `grep -n "amtcz sarif\|amtcz test\|amtcz exp" sdlc-kit/CLAUDE.md sdlc-kit/.claude/skills/run-build/SKILL.md sdlc-kit/.claude/skills/run-test/SKILL.md` | zero matches | fix-phase |
| AC-5 (no fallback, CLI deprecated-not-deleted) | manual read of the three rewritten docs for any "if MCP unavailable, use amtcz CLI" language; `amtcz-cli/README.md` diff | no fallback language found; deprecation note present | fix-phase |
| AC-6 (pytest coverage) | `pytest -q --collect-only` output vs. the 6 tools' verdict branches listed in Phase 3's steps | every branch enumerated in Phase 3.2-3.5 has a corresponding test | fix-phase adding the missing case |

## Regression Watchlist

- `amtcz-cli/amtcz.py` behavior must not change (it isn't touched at all —
  confirmed by the empty-diff check above).
- The experience-routing steps in `CLAUDE.md` outside the `amtcz`-specific
  lines (steps 1, 5, 7-10) must read identically before/after Phase 4 — only
  the tool-invocation mechanics change, not the routing logic itself.
- `run-build`/`run-test`'s non-`amtcz` content (Report Format prose, Rules
  section about paths/truncation/no-raw-logs) must survive Phase 4 intact —
  only the invocation + exit-code table lines change.
