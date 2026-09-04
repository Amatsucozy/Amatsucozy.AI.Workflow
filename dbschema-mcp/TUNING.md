# TUNING.md - dbschema-mcp calibration register

| Constant | Value | Rationale | Reversal signal |
|---|---|---|---|
| `W_TABLE_EXACT` | 40 | Whole-query == table name must outrank any accumulation of column hits (max column contribution per token = 3*3 = 9). | An exact-name table loses to a column-heavy table in observed use. |
| `W_TABLE_TOKEN` / `W_TABLE_SUBSTR` | 10 / 6 | Token equality beats substring so `order` prefers `Orders` over `OrderItems`, but substring still surfaces compound names. | Compound names (`OrderItems`) regularly needed but pushed below page cut. |
| `W_COLUMN_TOKEN` / `COLUMN_HIT_CAP` | 3 / 3 | Column hits are a weaker signal than names; cap stops wide tables (100+ columns) dominating every search. | Junction/link tables with only FK columns never surface for their referenced concepts. |
| `W_COMMENT_TOKEN` | 2 | Comments are often stale or absent; low weight, but non-zero so documented DBs benefit. | DB with rich MS_Description/COMMENT ON usage where comment hits are the only route to the right table. |
| `_stem` plural folding | strip `s`, `ies->y` | Table naming conventions split evenly between singular and plural. | False merges observed (e.g. `status` -> `statu`); switch to a token alias map. |
| `related()` depth cap | 4 | Beyond 4 hops the join graph in a normalised schema is effectively the whole DB. | Legit 5+ hop reporting joins requested more than once. |
| Snapshot on first call, no TTL | - | Schema changes are rare within a session; refresh is explicit (`catalog_refresh`). | Agents observed acting on stale schema after migrations in the same session -> add mtime/DDL-version probe. |
| Forced reload fails closed | - | `catalog_refresh` drops the snapshot before re-reading, so an unreachable database yields `catalog_unavailable` rather than pre-migration structure presented as current. Wrong schema silently is worse than no schema loudly. | Sessions repeatedly bricked by a transient connection blip that a retained snapshot would have ridden out. |
| No query execution | - | Server returns structure only; SQL authorship stays with the agent, blast radius stays zero. | Generated SQL fails on first run often enough that a `validate_sql` (EXPLAIN / `sp_describe_first_result_set`) tool pays for itself. |
