"""Index behaviour against a hand-built catalog. No DB, no mcp package needed.

The catalog itself and the `tbl` helper live in conftest.py — see the
sample_catalog docstring for which resolution case each table covers.
"""


def test_tokenize_folds_case_and_plural():
    from dbschema_mcp.catalog import tokenize
    assert tokenize("OrderItems") == ["order", "item"]
    assert tokenize("product_categories") == ["product", "category"]
    assert tokenize("address") == ["address"]


def test_search_tables_ranks_name_over_column(idx):
    hits = idx.search_tables("customer")
    assert hits[0].table == "dbo.Customers"
    assert "name:customer" in hits[0].matched_on
    assert any(h.table == "dbo.Orders" and "column:CustomerId" in h.matched_on for h in hits)


def test_search_tables_comment_match(idx):
    hits = idx.search_tables("billing")
    assert hits and hits[0].table == "dbo.Customers"


def test_search_columns_exact(idx):
    hits = idx.search_columns("total amount")
    assert hits[0].table == "dbo.Orders" and hits[0].column == "TotalAmount"
    assert "name:exact" in hits[0].matched_on


def test_resolve_bare_prefers_default_schema(idx):
    r = idx.resolve("orders")
    assert r.verdict == "ok" and r.table.qualified == "dbo.Orders"


def test_resolve_qualified_and_fuzzy(idx):
    assert idx.resolve("archive.Orders").table.qualified == "archive.Orders"
    assert idx.resolve("order_item").table.qualified == "dbo.OrderItems"
    assert idx.resolve("nothing").verdict == "not_found"


def test_resolve_ambiguous_when_no_default_schema_candidate(idx):
    r = idx.resolve("Products")
    assert r.verdict == "ambiguous" and r.table is None
    assert sorted(r.candidates) == ["archive.Products", "catalog.Products"]


def test_related_depth_and_direction(idx):
    orders = idx.resolve("dbo.Orders").table
    d1 = idx.related(orders, 1)
    by = {r.table: r for r in d1}
    assert by["dbo.Customers"].direction == "outbound"
    assert by["dbo.Customers"].join_on == "dbo.Orders.CustomerId = dbo.Customers.CustomerId"
    assert by["dbo.OrderItems"].direction == "inbound"
    assert "catalog.Products" not in by
    d2 = idx.related(orders, 2)
    prod = next(r for r in d2 if r.table == "catalog.Products")
    assert prod.distance == 2 and len(prod.path) == 2


def test_related_none(idx):
    assert idx.related(idx.resolve("archive.Orders").table, 3) == []
