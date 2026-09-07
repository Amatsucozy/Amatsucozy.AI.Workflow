"""In-memory index over a Catalog snapshot.

Answers the three question shapes the server is built for:
  "what table relates to X"        -> search_tables
  "what is the column name of Y"   -> search_columns
  "write a query to view entity Z" -> resolve + describe + related (join paths)

Scoring is deliberately mechanical: fixed integer weights, no model
judgement. Constants are listed in TUNING.md with reversal signals.
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field

from dbschema_mcp.model import Catalog, Table

# --- scoring constants (see TUNING.md) --------------------------------------
W_TABLE_EXACT = 40        # normalised whole query == table name
W_TABLE_TOKEN = 10        # query token == a token of the table name
W_TABLE_SUBSTR = 6        # query token is a substring of the joined table name
W_COLUMN_TOKEN = 3        # query token == a token of a column name (per column, capped)
W_COLUMN_SUBSTR = 2
W_COMMENT_TOKEN = 2       # query token appears in table/column comment
COLUMN_HIT_CAP = 3        # max column hits counted per table per token

W_COL_EXACT = 40
W_COL_TOKEN = 10
W_COL_SUBSTR = 6
W_COL_TABLE_TOKEN = 3     # token matches the owning table name (disambiguator)
W_COL_COMMENT = 2

_SPLIT = re.compile(r"[^a-z0-9]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize(text: str | None) -> list[str]:
    """snake_case, PascalCase, kebab, digits -> lower-cased tokens. Dedup-preserving order."""
    if not text:
        return []
    spaced = _CAMEL.sub(" ", text)
    seen: list[str] = []
    for tok in _SPLIT.split(spaced.lower()):
        tok = _stem(tok)
        if tok and tok not in seen:
            seen.append(tok)
    return seen


def _stem(tok: str) -> str:
    # minimal plural folding so "orders" hits "order" and "categories" hits "category"
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def _norm(text: str) -> str:
    return "".join(tokenize(text))


# --- results -----------------------------------------------------------------

@dataclass
class TableHit:
    table: str                # qualified
    kind: str
    score: int
    matched_on: list[str]     # human-readable reasons, e.g. "name:order", "column:customer_id"
    comment: str | None
    column_count: int


@dataclass
class ColumnHit:
    table: str
    column: str
    data_type: str
    nullable: bool
    is_pk: bool
    score: int
    matched_on: list[str]
    comment: str | None


@dataclass
class Relation:
    table: str                # qualified neighbour
    distance: int
    direction: str            # "outbound" (this table holds the FK) | "inbound" (neighbour holds the FK)
    via_fk: str
    join_on: str              # "a.schema.tbl.col = b.schema.tbl.col" pairs joined with AND
    path: list[str] = field(default_factory=list)  # join_on chain from the origin


@dataclass
class Resolution:
    verdict: str              # "ok" | "not_found" | "ambiguous"
    table: Table | None = None
    candidates: list[str] = field(default_factory=list)


# --- index -------------------------------------------------------------------

class SchemaIndex:
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self._by_bare: dict[str, list[Table]] = {}
        self._table_tokens: dict[str, list[str]] = {}
        self._adj: dict[str, list[tuple[str, str, str, str]]] = {}  # key -> [(neighbour_key, direction, fk_name, join_on)]
        for t in catalog.tables.values():
            self._by_bare.setdefault(t.name.lower(), []).append(t)
            self._table_tokens[t.key] = tokenize(t.name)
        self._build_graph()

    # -- name resolution --------------------------------------------------
    def resolve(self, name: str) -> Resolution:
        raw = name.strip().strip('[]"`')
        if "." in raw:
            schema, _, bare = raw.rpartition(".")
            key = f"{schema.strip('[]\"`')}.{bare.strip('[]\"`')}".lower()
            t = self.catalog.tables.get(key)
            return Resolution("ok", t) if t else Resolution("not_found")
        hits = self._by_bare.get(raw.lower(), [])
        if len(hits) == 1:
            return Resolution("ok", hits[0])
        if not hits:
            # tolerate plural/case/underscore drift: "OrderItems" vs "order_item"
            n = _norm(raw)
            fuzzy = [t for t in self.catalog.tables.values() if _norm(t.name) == n]
            if len(fuzzy) == 1:
                return Resolution("ok", fuzzy[0])
            if fuzzy:
                return Resolution("ambiguous", None, [t.qualified for t in fuzzy])
            return Resolution("not_found")
        # bare name exists in several schemas: prefer the dialect default schema
        default = [t for t in hits if t.schema.lower() == self.catalog.hints.default_schema.lower()]
        if len(default) == 1:
            return Resolution("ok", default[0])
        return Resolution("ambiguous", None, [t.qualified for t in hits])

    # -- search -----------------------------------------------------------
    def search_tables(self, query: str, max_results: int = 10) -> list[TableHit]:
        qtoks = tokenize(query)
        qnorm = _norm(query)
        hits: list[TableHit] = []
        for t in self.catalog.tables.values():
            score = 0
            reasons: list[str] = []
            ttoks = self._table_tokens[t.key]
            tjoined = "".join(ttoks)
            if qnorm and qnorm == tjoined:
                score += W_TABLE_EXACT
                reasons.append("name:exact")
            for q in qtoks:
                if q in ttoks:
                    score += W_TABLE_TOKEN
                    reasons.append(f"name:{q}")
                elif len(q) >= 3 and q in tjoined:
                    score += W_TABLE_SUBSTR
                    reasons.append(f"name~{q}")
                col_hits = 0
                for c in t.columns:
                    if col_hits >= COLUMN_HIT_CAP:
                        break
                    ctoks = tokenize(c.name)
                    if q in ctoks:
                        score += W_COLUMN_TOKEN
                        reasons.append(f"column:{c.name}")
                        col_hits += 1
                    elif len(q) >= 3 and q in "".join(ctoks):
                        score += W_COLUMN_SUBSTR
                        reasons.append(f"column~{c.name}")
                        col_hits += 1
                if q in tokenize(t.comment) or any(q in tokenize(c.comment) for c in t.columns if c.comment):
                    score += W_COMMENT_TOKEN
                    reasons.append(f"comment:{q}")
            if score:
                hits.append(TableHit(t.qualified, t.kind, score, reasons, t.comment, len(t.columns)))
        hits.sort(key=lambda h: (-h.score, h.table))
        return hits[:max_results]

    def search_columns(self, query: str, max_results: int = 20, table: str | None = None) -> list[ColumnHit]:
        qtoks = tokenize(query)
        qnorm = _norm(query)
        scope = list(self.catalog.tables.values())
        if table:
            r = self.resolve(table)
            scope = [r.table] if r.table else []
        hits: list[ColumnHit] = []
        for t in scope:
            ttoks = self._table_tokens[t.key]
            for c in t.columns:
                ctoks = tokenize(c.name)
                cjoined = "".join(ctoks)
                score = 0
                reasons: list[str] = []
                if qnorm and qnorm == cjoined:
                    score += W_COL_EXACT
                    reasons.append("name:exact")
                for q in qtoks:
                    if q in ctoks:
                        score += W_COL_TOKEN
                        reasons.append(f"name:{q}")
                    elif len(q) >= 3 and q in cjoined:
                        score += W_COL_SUBSTR
                        reasons.append(f"name~{q}")
                    if q in ttoks:
                        score += W_COL_TABLE_TOKEN
                        reasons.append(f"table:{q}")
                    if c.comment and q in tokenize(c.comment):
                        score += W_COL_COMMENT
                        reasons.append(f"comment:{q}")
                if score:
                    hits.append(ColumnHit(t.qualified, c.name, c.data_type, c.nullable, c.is_pk,
                                          score, reasons, c.comment))
        hits.sort(key=lambda h: (-h.score, h.table, h.column))
        return hits[:max_results]

    # -- FK graph ---------------------------------------------------------
    def _build_graph(self) -> None:
        for t in self.catalog.tables.values():
            for fk in t.foreign_keys:
                ref_key = f"{fk.ref_schema}.{fk.ref_table}".lower()
                ref = self.catalog.tables.get(ref_key)
                ref_q = ref.qualified if ref else f"{fk.ref_schema}.{fk.ref_table}"
                join_on = " AND ".join(
                    f"{t.qualified}.{a} = {ref_q}.{b}" for a, b in zip(fk.columns, fk.ref_columns))
                self._adj.setdefault(t.key, []).append((ref_key, "outbound", fk.name, join_on))
                self._adj.setdefault(ref_key, []).append((t.key, "inbound", fk.name, join_on))

    def related(self, table: Table, depth: int = 1, max_results: int = 50) -> list[Relation]:
        """BFS over FK edges, both directions. Distance-1 rows are the direct joins."""
        depth = max(1, min(depth, 4))
        seen = {table.key}
        queue: deque[tuple[str, int, list[str]]] = deque([(table.key, 0, [])])
        out: list[Relation] = []
        while queue and len(out) < max_results:
            key, dist, path = queue.popleft()
            if dist >= depth:
                continue
            for nkey, direction, fk_name, join_on in self._adj.get(key, []):
                if nkey in seen:
                    continue
                seen.add(nkey)
                nt = self.catalog.tables.get(nkey)
                npath = path + [join_on]
                out.append(Relation(nt.qualified if nt else nkey, dist + 1, direction, fk_name, join_on, npath))
                queue.append((nkey, dist + 1, npath))
        out.sort(key=lambda r: (r.distance, r.direction != "outbound", r.table))
        return out[:max_results]
