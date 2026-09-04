---
slug: forced-reload-must-fail-closed
use-when: "use when writing or reviewing a refresh/reload function that replaces cached state, especially one that can bail out on a precondition before attempting the reload"
domain: process
tags: [caching, refresh, stale-state, error-handling, mcp]
symptom: "refresh reports failure but subsequent reads still return the old cached value"
confidence: observed-once
date: 2026-09-04
source-task: adhoc-dbschema-mcp-review
---

# A reload that early-returns on a precondition leaves the stale value serving, while reporting failure

## Situation
`dbschema-mcp`'s `catalog_refresh` discards its in-memory database-schema
snapshot and re-introspects. Its loader cleared the cache on the exception
path but *early-returned* on the missing-config path before touching it. So a
refresh with no `DBSCHEMA_URL` correctly returned `catalog_unavailable` — and
then every subsequent tool call happily answered from the pre-refresh
snapshot.

## Lesson
In a `load(force=True)`-shaped function, clear the cached value at the top of
the forced branch, before any precondition check that can return early —
not inside the error handler of the reload attempt. Error handlers only cover
the failures you routed through them; guard clauses (missing config, empty
input, feature flag off) return *before* them and silently preserve the very
state the caller asked you to discard. The caller asked for a refresh and got
a failure verdict, so it reasonably assumes there is now no data — but reads
keep succeeding with stale data, which is strictly worse than an outage:
wrong-and-confident beats absent only for the person measuring uptime. Decide
the fail-closed policy once, implement it as the first statement in the forced
path, and write the test as *"failed refresh → subsequent read also fails"*,
never just *"failed refresh returns an error"* — the second assertion is the
one that catches this.

## Evidence
`dbschema-mcp/src/dbschema_mcp/server.py` `_load()`: `if not url: _load_error
= ...; return None` sat above the `try/except` whose handler did set `_index =
None`. Fixed by adding `if force: _index = None` immediately after the
cache-hit check. Found only because the amtcz convention's
`tests/test_server.py` was being added (see
`amtcz-mcp-server-package-convention`) — the six pre-existing unit tests
covered indexing logic and passed throughout; the bug lived in the
tool/lifecycle seam none of them touched. Test that pins it:
`test_catalog_refresh_reloads_and_fails_closed`, which asserts the *second*
call fails too.

## Applies When / Not When
Applies to any explicit-refresh API over cached state where the caller reads
the outcome and then continues issuing reads — config reloaders, schema and
metadata snapshots, token/credential caches. The fail-closed choice is correct
where stale data is actively misleading (schema after a migration, permissions
after a revocation). It is the wrong default where the cache is a latency
optimisation over data that doesn't go dangerously stale and availability
matters more — there, keep the old value and surface staleness via a timestamp
instead. Either way the rule holds: choose deliberately and make the guard
clause obey the same policy as the exception handler.
