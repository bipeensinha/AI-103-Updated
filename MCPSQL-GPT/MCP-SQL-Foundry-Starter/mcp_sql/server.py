"""Read-only SQL Server MCP server. Runs locally over MCP STDIO."""
import os, re
from pathlib import Path
from typing import Any
import pyodbc
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).resolve().parent / ".env")
mcp = FastMCP("onprem-sql-readonly")

def required(key, default=None):
    value = os.getenv(key, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing environment variable: {key}")
    return value

def connect():
    driver = required("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    server, port = required("SQL_SERVER"), os.getenv("SQL_PORT", "1433")
    database = required("SQL_DATABASE")
    encrypt = os.getenv("SQL_ENCRYPT", "yes")
    trust = os.getenv("SQL_TRUST_SERVER_CERTIFICATE", "no")
    if os.getenv("SQL_AUTH_MODE", "sql").lower() == "windows":
        cs = (f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};"
              f"Trusted_Connection=yes;Encrypt={encrypt};TrustServerCertificate={trust};")
    else:
        cs = (f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};"
              f"UID={required('SQL_USERNAME')};PWD={required('SQL_PASSWORD')};"
              f"Encrypt={encrypt};TrustServerCertificate={trust};")
    return pyodbc.connect(cs, timeout=int(os.getenv("SQL_CONNECTION_TIMEOUT", "8")))

def rows_as_dicts(cursor, rows):
    names = [c[0] for c in cursor.description or []]
    output = []
    for row in rows:
        item = {}
        for name, value in zip(names, row):
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif isinstance(value, (bytes, bytearray)):
                value = f"<binary data: {len(value)} bytes>"
            item[name] = value
        output.append(item)
    return output

@mcp.tool()
def test_sql_connection() -> dict:
    """Test SQL connectivity and report server, database and login."""
    with connect() as cn:
        row = cn.cursor().execute(
            "SELECT @@SERVERNAME, DB_NAME(), SUSER_SNAME()"
        ).fetchone()
        return {"connected": True, "server": row[0], "database": row[1], "login": row[2]}

@mcp.tool()
def list_tables(schema_name: str = "dbo") -> dict:
    """List base tables in a schema, default dbo."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", schema_name):
        raise ValueError("Invalid schema name")
    sql = """SELECT TABLE_SCHEMA AS schema_name, TABLE_NAME AS table_name
             FROM INFORMATION_SCHEMA.TABLES
             WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA=?
             ORDER BY TABLE_NAME"""
    with connect() as cn:
        cur = cn.cursor()
        rows = cur.execute(sql, schema_name).fetchall()
        return {"tables": rows_as_dicts(cur, rows)}

@mcp.tool()
def describe_table(table_name: str, schema_name: str = "dbo") -> dict:
    """List column names, SQL types and nullability for a table."""
    for value in (table_name, schema_name):
        if not re.fullmatch(r"[A-Za-z0-9_]+", value):
            raise ValueError("Invalid table or schema name")
    sql = """SELECT COLUMN_NAME AS column_name, DATA_TYPE AS data_type,
                    CHARACTER_MAXIMUM_LENGTH AS max_length, IS_NULLABLE AS is_nullable
             FROM INFORMATION_SCHEMA.COLUMNS
             WHERE TABLE_SCHEMA=? AND TABLE_NAME=? ORDER BY ORDINAL_POSITION"""
    with connect() as cn:
        cur = cn.cursor()
        rows = cur.execute(sql, schema_name, table_name).fetchall()
        return {"schema": schema_name, "table": table_name,
                "columns": rows_as_dicts(cur, rows)}

@mcp.tool()
def run_readonly_query(sql: str, max_rows: int = 100) -> dict:
    """Execute one SELECT query only. Results are capped at 100 rows."""
    if not sql or len(sql) > 8000:
        raise ValueError("SQL is empty or exceeds 8000 characters")
    query = sql.strip()
    if not re.match(r"(?is)^SELECT\b", query):
        raise ValueError("Only SELECT statements are permitted")
    if ";" in query.rstrip(";") or re.search(
        r"(?i)\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT|REVOKE|DENY|DBCC|WAITFOR|OPENROWSET)\b",
        query
    ) or any(token in query for token in ("--", "/*", "*/")):
        raise ValueError("Only a single plain SELECT statement is permitted")
    max_rows = max(1, min(int(max_rows), 100))
    if not re.match(r"(?is)^SELECT\s+(DISTINCT\s+)?TOP\s*\\(", query):
        query = re.sub(r"(?is)^SELECT\s+", f"SELECT TOP ({max_rows}) ", query, count=1)
    with connect() as cn:
        cur = cn.cursor()
        cur.timeout = int(os.getenv("SQL_QUERY_TIMEOUT", "15"))
        cur.execute(query)
        rows = cur.fetchmany(max_rows)
        data = rows_as_dicts(cur, rows)
        return {"row_count": len(data), "max_rows": max_rows,
                "rows": data, "limit_reached": len(data) >= max_rows}

if __name__ == "__main__":
    mcp.run(transport="stdio")
