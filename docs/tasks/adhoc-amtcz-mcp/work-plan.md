## Strategy

Vendor the CLI's *pure data-extraction* functions (`load_diagnostics`,
`find_sarif_files`, `parse_trx_failures`, `read_trx_summary`, `load_entries`,
`parse_frontmatter`, etc. — research's "Reuse Classification" table) almost
verbatim into three new modules, one per domain (SARIF/TRX/experiences).
The CLI's *mixed print+logic* functions (`run_probe`, `trx_report`,
`cmd_sarif_build`, `cmd_test_run`, `cmd_exp_inventory`, `cmd_exp_search`)
cannot be reused as-is regardless of the dependency decision — they conflate
"compute the verdict" with "print an ASCII table" — so each is reimplemented
to return a dataclass (verdict + data) instead of printing, then wired to an
MCP tool. Rejected alternative: depend on `amtcz-cli` and refactor it in
place to expose structured functions. Rejected because the user confirmed
`amtcz-cli` is being retired — adding a shared dependency between the two
packages just before one is deleted creates churn for no lasting benefit.

MCP server built with the official `mcp` Python SDK's `FastMCP` (stdio
transport, decorator-registered tools) — each tool's Python docstring and
typed parameters become its MCP description, which is the "simple
instruction surface" the user asked for (agent sees the tool list + built-in
descriptions, no separate flag manual needed).

Verification note (flagged for approval): the kit's `run-build`/`run-test`
skills are .NET-specific (SARIF/TRX extraction) and don't apply to testing
Python code. There is no Python-test skill in this kit, so the reviewer gate
runs `pytest` directly via Bash — output is a small pass/fail summary, not
raw logs, so this stays within the spirit of the Hard Rule (cap what enters
context) even though it doesn't go through `run-test`.

## Phase 1 — Vendored extraction modules (SARIF, TRX, experiences)

Goal: Three pure-Python modules exist, each holding the parsing/extraction
logic for one domain, returning dataclasses instead of printing.

Executor: engineer

Scope:
- `amtcz-mcp/pyproject.toml` (new)
- `amtcz-mcp/src/amtcz_mcp/__init__.py` (new)
- `amtcz-mcp/src/amtcz_mcp/sarif.py` (new)
- `amtcz-mcp/src/amtcz_mcp/trx.py` (new)
- `amtcz-mcp/src/amtcz_mcp/experiences.py` (new)

| Step | Action | File | Anchor | Done-when |
|---|---|---|---|---|
| 1.1 | Create package skeleton: `[build-system]` setuptools, `[project]` name `amtcz-mcp`, `requires-python >=3.10`, dependency `mcp>=1.0`, `[project.scripts] amtcz-mcp = "amtcz_mcp.server:main"`, `[project.optional-dependencies] dev = ["pytest"]`, src-layout (`[tool.setuptools.packages.find] where = ["src"]`) | `amtcz-mcp/pyproject.toml` | reference shape: `amtcz-cli/pyproject.toml` (research L23) | `pip install -e .` (or `pip install -e ".[dev]"`) resolves without error |
| 1.2 | Port `uri_to_rel`, `load_diagnostics`, `find_sarif_files`, `CASCADE_CODES`, `BUILD_PROPERTY` near-verbatim from `amtcz.py` L74-125. Add `@dataclass SarifDiagnostic {level,code,file,line,msg}` and `@dataclass SarifReport {log_count,verdict:Literal["no_logs","clean","errors_found"],errors:list[SarifDiagnostic],warnings:list[SarifDiagnostic],total_errors:int,truncated:bool,first_error:SarifDiagnostic\|None,cascade_count:int,cascade_verdict:str\|None}`. Add `extract_sarif_report(root,pattern,max_rows,include_warnings) -> SarifReport` replacing `run_probe`'s logic (amtcz.py L128-181) minus all `out()` calls. | `amtcz-mcp/src/amtcz_mcp/sarif.py` | `amtcz-cli/amtcz.py` L69-181 | `extract_sarif_report()` importable and callable against a hand-built temp dir with a sample SARIF file, returns a `SarifReport` with correct `verdict` |
| 1.3 | Add `@dataclass SarifBuildResult {build_exit:int,dotnet_found:bool,console_tail:list[str],logs_fresh:int,logs_carried:int,report:SarifReport\|None,verdict:Literal["success","errors_found","no_sarif_logs","gap_msbuild_failure","dotnet_not_found"]}` and `run_sarif_build(root,target,pattern,max_rows,include_warnings,rebuild) -> SarifBuildResult`, porting `clean_all_sarif` + `cmd_sarif_build`'s orchestration (amtcz.py L188-268) minus `out()` calls — same mtime fresh/carried snapshot logic, same verdict derivation (build exit vs `extract_sarif_report`'s verdict) collapsed into the five-way `verdict` enum matching the CLI's exit 0-4 meanings one-to-one. | `amtcz-mcp/src/amtcz_mcp/sarif.py` | `amtcz-cli/amtcz.py` L188-268 | function exists, `dotnet not found` path returns `verdict="dotnet_not_found"` when `shutil.which("dotnet")` is mocked to `None` |
| 1.4 | Port `_first_repo_frame`, `_exception_type`, `parse_trx_failures`, `read_trx_summary`, `TRX_NS`, `TRX_FILENAME`, `STACK_FRAME_RE`, `FAILURE_OUTCOMES` near-verbatim from amtcz.py L275-372. Add `@dataclass TrxFailure {name,class_,outcome,message,location:tuple[str,int]\|None}` and `@dataclass TrxReport {verdict:Literal["no_trx","zero_discovered","pass","fail"],total:int,passed:int,failed:int,other:int,failures:list[TrxFailure],truncated:bool,cluster_verdict:str\|None}`. Add `extract_trx_report(trx_path,root,max_rows) -> TrxReport` replacing `trx_report` (amtcz.py L375-430) minus `out()` calls. | `amtcz-mcp/src/amtcz_mcp/trx.py` | `amtcz-cli/amtcz.py` L271-430 | `extract_trx_report()` importable, returns correct `verdict` for a hand-built sample `.trx` fixture string |
| 1.5 | Add `@dataclass TestRunResult {test_exit:int,dotnet_found:bool,console_tail:list[str],report:TrxReport\|None,verdict:Literal["pass","fail","no_trx","zero_discovered","dotnet_not_found"]}` and `run_test(root,target,results_dir,no_build,filter_expr,max_rows) -> TestRunResult`, porting `cmd_test_run`'s orchestration (amtcz.py L433-472) minus `out()` calls. | `amtcz-mcp/src/amtcz_mcp/trx.py` | `amtcz-cli/amtcz.py` L433-472 | function exists, `dotnet not found` path returns `verdict="dotnet_not_found"` |
| 1.6 | Port `strip_comment`, `parse_frontmatter`, `load_entries`, `AXIS_WEIGHT` near-verbatim from amtcz.py L485-553. Add `@dataclass ExpEntry` mirroring the frontmatter dict shape (slug, use_when, domain, tags, symptom, confidence, date, source_task, path) and `@dataclass ExpInventoryResult {verdict:Literal["no_entries","ok"],entry_count:int,tag_counts:dict[str,int],malformed:list[str]}`, `@dataclass ExpSearchHit {slug,matched_on:list[str],use_when,path,score:int}`, `@dataclass ExpSearchResult {verdict:Literal["no_entries","usage_error","ok"],total_hits:int,hits:list[ExpSearchHit],truncated:bool,malformed:list[str]}`. Add `inventory(root) -> ExpInventoryResult` (replaces `cmd_exp_inventory`, amtcz.py L565-583) and `search(root,tags,symptom,keywords,max_rows) -> ExpSearchResult` (replaces `cmd_exp_search`, amtcz.py L586-644), both minus `out()` calls. | `amtcz-mcp/src/amtcz_mcp/experiences.py` | `amtcz-cli/amtcz.py` L481-644 | `inventory()`/`search()` importable, return correct `verdict` against a temp `docs/experiences/*.md` fixture tree |

Exit state: three importable modules with zero MCP/server dependency,
individually exercisable from a Python REPL or test file; no CLI code
touched.

## Phase 2 — MCP server, packaging, Docker

Goal: `amtcz-mcp` starts as a stdio MCP server exposing the 6 tools with
self-documenting descriptions; a Docker image builds and runs it.

Executor: engineer

Scope:
- `amtcz-mcp/src/amtcz_mcp/server.py` (new)
- `amtcz-mcp/Dockerfile` (new)
- `amtcz-mcp/README.md` (new)
- `amtcz-mcp/pyproject.toml` (edit — confirm entry point matches `server.py`'s `main`)

| Step | Action | File | Anchor | Done-when |
|---|---|---|---|---|
| 2.1 | `from mcp.server.fastmcp import FastMCP; mcp = FastMCP("amtcz")`. Register 6 `@mcp.tool()` functions — `sarif_build`, `sarif_probe`, `test_run`, `test_probe`, `exp_inventory`, `exp_search` — typed params matching each CLI flag (research's "Detailed Exit Code & Flag Inventory" per-op flag list; e.g. `sarif_build(root: str = ".", target: str \| None = None, pattern: str = "**/obj/**/msbuild.sarif", max_rows: int = 30, warnings: bool = False, rebuild: bool = False)`), each with a docstring stating: what it does, what `verdict` values mean (spelling out the old exit-code semantics in prose), and when to prefer it over its sibling (`probe` vs `build`/`run` — never re-run to re-read). Each handler calls its Phase-1 function and returns `dataclasses.asdict(result)`. Add `def main(): mcp.run(transport="stdio")`. | `amtcz-mcp/src/amtcz_mcp/server.py` | Phase 1 dataclasses/functions; tool docstring content mirrors CLAUDE.md L122-210's per-command prose (research) so nothing is lost, just relocated | `python -c "from amtcz_mcp.server import mcp; print(sorted(t.name for t in mcp._tool_manager.list_tools()))"` (or equivalent FastMCP introspection) prints exactly the 6 tool names |
| 2.2 | `FROM mcr.microsoft.com/dotnet/sdk:8.0`; `apt-get update && apt-get install -y python3 python3-pip --no-install-recommends`; `COPY . /app`; `WORKDIR /app`; `RUN pip install --break-system-packages .`; `WORKDIR /workspace`; `ENTRYPOINT ["amtcz-mcp"]`. | `amtcz-mcp/Dockerfile` | — | `docker build -t amtcz-mcp amtcz-mcp/` succeeds (if Docker is available in the verification environment — see verification plan) |
| 2.3 | Document: what amtcz-mcp is (successor to amtcz-cli, which is deprecated — cross-reference), building the image, running it with a target repo mounted (`docker run -i --rm -v "$(pwd):/workspace" amtcz-mcp`), registering it in a consumer's `.mcp.json` (stdio command = the docker run line), and the 6 tools at a glance (name + one-line purpose — full docs live in the tool descriptions themselves, not restated here). | `amtcz-mcp/README.md` | `amtcz-cli/README.md` (structure precedent, not content) | file exists, covers build/run/register/tool-list |

Exit state: a working, buildable MCP server package; `amtcz-cli/` untouched.

## Phase 3 — pytest suite

Goal: every one of the 6 tool-facing functions is covered across its
distinct verdict branches; suite passes without requiring Docker or a real
`dotnet` install (subprocess calls mocked).

Executor: engineer

Scope:
- `amtcz-mcp/tests/conftest.py` (new)
- `amtcz-mcp/tests/fixtures/sample.sarif` (new)
- `amtcz-mcp/tests/fixtures/sample.trx` (new)
- `amtcz-mcp/tests/fixtures/experiences/*.md` (new, 2-3 small sample entries incl. one malformed)
- `amtcz-mcp/tests/test_sarif.py` (new)
- `amtcz-mcp/tests/test_trx.py` (new)
- `amtcz-mcp/tests/test_experiences.py` (new)
- `amtcz-mcp/tests/test_server.py` (new)

| Step | Action | File | Anchor | Done-when |
|---|---|---|---|---|
| 3.1 | Fixture files: one SARIF JSON with 1 error + 1 warning row, one empty-results SARIF; one `.trx` XML with 1 failed + 1 passed test, one with 0 discovered; 3 experience `.md` files (2 well-formed with distinct tags, 1 with unclosed frontmatter). | `amtcz-mcp/tests/fixtures/**` | research's table-column notes per op | fixtures load without exceptions in a scratch script |
| 3.2 | `test_sarif.py`: `extract_sarif_report` against no-files dir (verdict `no_logs`), clean-fixture dir (verdict `clean`), error-fixture dir (verdict `errors_found`, checks `first_error`/`cascade_verdict`/`truncated` with a `max_rows` small enough to force truncation). `run_sarif_build` with `subprocess.run` mocked (patch `amtcz_mcp.sarif.subprocess.run`) for: exit 0 + errors-fixture SARIF → `errors_found`; exit 0 + no logs → `no_sarif_logs`; nonzero exit + clean SARIF → `gap_msbuild_failure`; `shutil.which` mocked to `None` → `dotnet_not_found`. | `amtcz-mcp/tests/test_sarif.py` | Phase 1.2/1.3 | `pytest amtcz-mcp/tests/test_sarif.py` all pass |
| 3.3 | `test_trx.py`: `extract_trx_report` against missing path (`no_trx`), zero-discovered fixture (`zero_discovered`), pass fixture (`pass`), fail fixture (`fail`, checks `failures`/`cluster_verdict`). `run_test` with `subprocess.run` mocked for pass/fail/no-trx cases and `shutil.which` mocked to `None` for `dotnet_not_found`. | `amtcz-mcp/tests/test_trx.py` | Phase 1.4/1.5 | `pytest amtcz-mcp/tests/test_trx.py` all pass |
| 3.4 | `test_experiences.py`: `inventory` against empty dir (`no_entries`) and fixture dir (`ok`, correct `tag_counts`, malformed file listed). `search` against empty dir (`no_entries`), no-search-flags call (`usage_error`), and a real query hitting the fixtures (`ok`, correct `hits`/scoring order per `AXIS_WEIGHT`). | `amtcz-mcp/tests/test_experiences.py` | Phase 1.6 | `pytest amtcz-mcp/tests/test_experiences.py` all pass |
| 3.5 | `test_server.py`: import `amtcz_mcp.server`, assert the 6 registered tool names, and for at least `sarif_probe`/`exp_inventory` call the tool handler function directly against a fixture dir, asserting the returned dict has the expected `verdict` key/value (confirms the `dataclasses.asdict` wiring, not just the underlying function). | `amtcz-mcp/tests/test_server.py` | Phase 2.1 | `pytest amtcz-mcp/tests/test_server.py` all pass |

Exit state: `cd amtcz-mcp && pytest -q` is green; no network, Docker, or
`dotnet` install required to run the suite.

## Phase 4 — Migrate kit docs off the amtcz CLI

Goal: `CLAUDE.md` and the two skills reference the MCP tools by name; no
remaining prose tells an agent to run `amtcz <subcommand>`.

Executor: engineer

Scope:
- `sdlc-kit/CLAUDE.md` (edit)
- `sdlc-kit/.claude/skills/run-build/SKILL.md` (edit)
- `sdlc-kit/.claude/skills/run-test/SKILL.md` (edit)
- `amtcz-cli/README.md` (edit — deprecation note only)

| Step | Action | File | Anchor | Done-when |
|---|---|---|---|---|
| 4.1 | Routing steps: replace the L18 `amtcz exp inventory` command with a call to the `exp_inventory` tool (verdict `no_entries` = old exit 2 → same "skip straight to step 6" branch); replace L33's `amtcz exp search ...` with the `exp_search` tool (same param names: `tag`/`symptom`/`keyword`). Replace L58's PATH note with an equivalent statement that the MCP server must be registered/reachable for subagent tool calls too (a subagent that finds the tools absent reports `blocked`, decision belongs to the human — same governance, new mechanism). | `sdlc-kit/CLAUDE.md` | research L18,33,58 | grep for literal `amtcz ` command invocations in these lines returns nothing; tool names appear instead |
| 4.2 | Replace the L65-210 "Reference — amtcz CLI" block (guarantee header, Quick-Reference scenario tables, six per-command sections) with a short "Reference — amtcz-mcp tools" block: one paragraph stating the tools are self-describing (agent sees name+description+schema once the server is registered — no need to memorize flags here) plus the *scenario* guidance that isn't in a tool description by nature (e.g. "probe, don't rebuild, to re-read after truncation" / "`--rebuild` only on explicit human request" cross-tool judgment calls) and the same verdict-to-action table content, now keyed by `verdict` string instead of exit code. | `sdlc-kit/CLAUDE.md` | research L65-210 | section is materially shorter than the original (no per-flag prose duplicating what Phase 2.1's docstrings already say); verdict-to-action guidance preserved |
| 4.3 | Replace the `amtcz sarif build`/`amtcz sarif probe` Bash invocations (L28, L41) and the exit-code table (L30-37) with calls to the `sarif_build`/`sarif_probe` tools and a verdict-string table (`success`/`errors_found`/`no_sarif_logs`/`gap_msbuild_failure`/`dotnet_not_found`) mapped to the same "Then" actions. Update L16's "guaranteed installed and is the only path" framing to the MCP-server equivalent (server registered, no fallback) and L19's CLAUDE.md pointer to name the new Reference block. L53's "the amtcz table verbatim" becomes "the tool's `errors`/`warnings` list, formatted as a table" (the report format the skill hands to the human is still a table — only the wire format from the tool changed). | `sdlc-kit/.claude/skills/run-build/SKILL.md` | research (run-build rows) | no literal `amtcz ` Bash invocation remains; exit-code table replaced 1:1 by verdict-string table |
| 4.4 | Same treatment as 4.3, mirrored for `test_run`/`test_probe`: L27, L29-36, L39, L14, L18, L48. | `sdlc-kit/.claude/skills/run-test/SKILL.md` | research (run-test rows) | no literal `amtcz ` Bash invocation remains; exit-code table replaced 1:1 by verdict-string table |
| 4.5 | Add a short "Status" note near the top: deprecated, superseded by `amtcz-mcp` (link), kept installable but no longer the kit's documented interface. No other content in this file changes (Consumers section, Changelog, Usage block stay as historical record). | `amtcz-cli/README.md` | research L116-130 | note present; rest of file diff is empty |

Exit state: the three consumer docs are internally consistent with
`amtcz-mcp`'s actual tool names/params/verdicts from Phases 1-2;
`amtcz-cli/amtcz.py` has zero diff.

## Phase 3a — Fix: missing test_run zero_discovered coverage (Gate G2 fix-phase)

Goal: AC-6 gap closed — `test_run`'s `zero_discovered` verdict has wrapper-level
test coverage matching its four sibling verdicts.

Executor: engineer

Scope:
- `amtcz-mcp/tests/test_trx.py` (edit only)

Cause: Gate G2 review found `trx.run_test()` (the function the `test_run` MCP
tool actually calls) has no test asserting `verdict == "zero_discovered"` —
only the lower-level `extract_trx_report()` has one. The other four `run_test`
verdicts (`pass`/`fail`/`no_trx`/`dotnet_not_found`) all have wrapper-level
tests already.

| Step | Action | File | Done-when |
|---|---|---|---|
| 3a.1 | Add `test_run_test_zero_discovered`, mirroring the existing `test_run_test_pass`/`test_run_test_fail` pattern: mock `subprocess.run` so the zero-discovered TRX fixture (already defined in the file) is what `run_test()` reads back, call `trx.run_test(...)`, assert `result.verdict == "zero_discovered"`. | `amtcz-mcp/tests/test_trx.py` | `pytest -q` shows 30 passed (29 + this one), 0 failures |

Re-gate: rerun `pytest -q` (full suite) and re-confirm AC-6 only — no other AC
needs re-checking.

## Explicitly Not Doing

- Not touching `bin/index.js` / `package.json` `files` — no npx-installer
  auto-registration of the MCP server (ticket Constraints).
- Not deleting or functionally changing `amtcz-cli/amtcz.py` — deprecation
  note only (ticket AC-5).
- Not adding a CLI-fallback section to any rewritten doc (ticket AC-5).
- Not touching `sdlc-kit/MIGRATION.md`, `TUNING.md`, `SESSION.md`, or the
  root `README.md` (ticket Non-goal) — if implementation surfaces a hard
  inconsistency in one of these, report it rather than silently expanding
  scope.
- Not building HTTP/SSE transport — stdio only (ticket Constraints).
