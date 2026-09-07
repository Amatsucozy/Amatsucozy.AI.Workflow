"""Shared pytest fixtures for the dbschema-mcp test suite.

The whole suite runs against a hand-built Catalog — no database, no driver,
and (for everything but test_server.py) no `mcp` package needed. Providers
are exercised only for URL parsing and type rendering, which are pure.
"""
from __future__ import annotations

import pytest

from dbschema_mcp.catalog import SchemaIndex
from dbschema_mcp.model import Catalog, Column, DialectHints, ForeignKey, Table

HINTS = DialectHints("mssql", "[", "]", "dbo", "TOP (<n>)", "+")


def tbl(schema, name, cols, pk=(), fks=(), comment=None) -> Table:
    """A Table with int columns named by `cols`, PK flags set from `pk`."""
    return Table(schema, name, "table", comment,
                 [Column(c, "int", True, is_pk=c in pk, ordinal=i) for i, c in enumerate(cols, 1)],
                 list(pk), list(fks))


@pytest.fixture
def sample_catalog() -> Catalog:
    """A small mssql-shaped catalog covering every resolution case the tools
    have a verdict for:

      dbo.Orders / archive.Orders     bare name in 2 schemas, one of them the
                                      dialect default -> resolves to dbo
      catalog.Products / archive.Products
                                      bare name in 2 schemas, neither default
                                      -> ambiguous
      archive.Orders                  no FK edges -> no_relations
      dbo.Orders -> dbo.Customers     outbound FK
      dbo.OrderItems -> dbo.Orders    inbound FK from Orders' point of view
      dbo.OrderItems -> catalog.Products
                                      cross-schema, reachable from Orders at
                                      distance 2
    """
    tables = [
        tbl("dbo", "Customers", ["CustomerId", "CustomerName", "Email"], pk=["CustomerId"],
            comment="Billing account holders"),
        tbl("dbo", "Orders", ["OrderId", "CustomerId", "OrderDate", "TotalAmount"], pk=["OrderId"],
            fks=[ForeignKey("FK_Orders_Customers", ["CustomerId"], "dbo", "Customers",
                            ["CustomerId"])]),
        tbl("dbo", "OrderItems", ["OrderItemId", "OrderId", "ProductId", "Quantity"],
            pk=["OrderItemId"],
            fks=[ForeignKey("FK_OrderItems_Orders", ["OrderId"], "dbo", "Orders", ["OrderId"]),
                 ForeignKey("FK_OrderItems_Products", ["ProductId"], "catalog", "Products",
                            ["ProductId"])]),
        tbl("catalog", "Products", ["ProductId", "Sku", "ProductName"], pk=["ProductId"]),
        tbl("archive", "Products", ["ProductId"], pk=["ProductId"]),
        tbl("archive", "Orders", ["OrderId"], pk=["OrderId"]),
    ]
    return Catalog("mssql", "shop", HINTS, {t.key: t for t in tables},
                   "2026-09-04T00:00:00+00:00")


@pytest.fixture
def idx(sample_catalog) -> SchemaIndex:
    """SchemaIndex over sample_catalog."""
    return SchemaIndex(sample_catalog)
