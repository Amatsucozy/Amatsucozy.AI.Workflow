from dbschema_mcp.providers import detect_dialect
from dbschema_mcp.providers.mssql import build_odbc_string, render_type


def test_detect():
    assert detect_dialect("postgresql://u:p@h/db") == "postgres"
    assert detect_dialect("mssql://h/db") == "mssql"
    assert detect_dialect("Driver={x};Server=h;Database=d") == "mssql"


def test_url_to_odbc():
    s = build_odbc_string("mssql://sa:p%40ss@db.local:1433/Shop?TrustServerCertificate=yes")
    assert "Server=db.local,1433" in s and "Database=Shop" in s
    assert "Uid=sa" in s and "Pwd=p@ss" in s and "trustservercertificate=yes" in s
    assert "Driver={ODBC Driver 18 for SQL Server}" in s
    t = build_odbc_string("mssql://db.local/Shop")
    assert "trusted_connection=yes" in t and "Uid=" not in t


def test_render_type():
    assert render_type("nvarchar", -1, 0, 0) == "nvarchar(max)"
    assert render_type("nvarchar", 100, 0, 0) == "nvarchar(50)"
    assert render_type("decimal", 9, 18, 2) == "decimal(18,2)"
    assert render_type("datetime2", 8, 27, 7) == "datetime2(7)"
    assert render_type("int", 4, 10, 0) == "int"
