# db_controller.py - Database Controller Module

## File Location
```
nl2sql_assistant/src/database/db_controller.py
```

## Purpose
This module provides a comprehensive interface for all PostgreSQL database operations. It handles:
- Database connections with automatic reconnection
- Query execution with error handling
- Schema introspection (table names, column info)
- Connection lifecycle management

---

## Dependencies

```python
import psycopg2                    # PostgreSQL adapter for Python
import pandas as pd                # DataFrames for query results
from typing import Union           # Type hints
import sys, os                     # Path manipulation
from sqlalchemy import create_engine  # SQLAlchemy engine for pandas
import warnings                    # Suppress deprecation warnings

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import DB_CONFIG
from src.utils.logger import logger, log_db, log_error
```

### Why These Dependencies?

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **psycopg2** | PostgreSQL connection | Most popular, battle-tested, supports all PG features |
| **pandas** | Query results as DataFrame | Easy data manipulation, display, export |
| **SQLAlchemy** | Engine for pandas.read_sql | pandas prefers SQLAlchemy connections |

### Why Both psycopg2 AND SQLAlchemy?

```python
# psycopg2 is used for:
self.conn = psycopg2.connect(...)  # Direct connection
cursor = self.conn.cursor()        # Execute non-SELECT statements
self.conn.commit()                 # Transaction control

# SQLAlchemy engine is used for:
self.engine = create_engine(...)   # pandas read_sql requires this
df = pd.read_sql_query(sql, self.engine)  # Returns DataFrame
```

**Reason**: pandas deprecated passing raw connections, now requires SQLAlchemy engines. We keep psycopg2 for direct execution (INSERT, UPDATE, DDL).

---

## Class: DatabaseController

### Constructor: `__init__`

```python
def __init__(self, dbname=None, user=None, password=None, host=None, port=None):
    self.dbname = dbname or DB_CONFIG.get('dbname', 'nl2sql_db')
    self.user = user or DB_CONFIG.get('user', 'postgres')
    self.password = password or DB_CONFIG.get('password', 'postgres')
    self.host = host or DB_CONFIG.get('host', 'localhost')
    self.port = port or DB_CONFIG.get('port', 5432)
    self.conn = None
    self.engine = None
```

#### Parameter Priority:
1. **Explicit parameters** (if passed to constructor)
2. **DB_CONFIG** values (from config.py)
3. **Hardcoded defaults** (fallback)

This allows:
```python
# Use config defaults
db = DatabaseController()

# Override specific values
db = DatabaseController(dbname='other_db', port=5433)
```

---

### Method: `connect()`

Establishes connection to PostgreSQL and creates SQLAlchemy engine.

```python
def connect(self):
    try:
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

        connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        self.engine = create_engine(connection_string)

        return True
    except psycopg2.OperationalError as e:
        # Connection refused, auth failed, DB not found
        return False
```

#### Connection String Format:
```
postgresql://username:password@host:port/database
Example: postgresql://postgres:postgres@localhost:5432/nl2sql_db
```

#### Error Handling:

| Exception | Cause | User Message |
|-----------|-------|--------------|
| **OperationalError** | Server offline, wrong credentials, DB not found | "Make sure PostgreSQL is running..." |
| **Exception** | Unexpected errors | Generic error message |

---

### Method: `execute_query(sql)` → DataFrame or str

The primary method for running SELECT queries. Returns results as a pandas DataFrame.

```python
def execute_query(self, sql: str) -> Union[pd.DataFrame, str]:
    try:
        if not self.conn or self.conn.closed:
            if not self.connect():
                return "Error: Cannot connect to database"

        df = pd.read_sql_query(sql, self.engine)
        return df

    except psycopg2.Error as e:
        return f"Database Error: {str(e)}"
    except pd.io.sql.DatabaseError as e:
        return f"Query Error: {str(e)}"
```

#### Return Type Logic:

```
┌─────────────────────────────────┐
│ execute_query(sql)              │
└───────────────┬─────────────────┘
                │
                ▼
         ┌──────────────┐
         │ Connection   │
         │ alive?       │
         └──────┬───────┘
                │
       ┌────────┴────────┐
       │                 │
  ┌────▼────┐       ┌────▼────┐
  │   Yes   │       │   No    │
  └────┬────┘       └────┬────┘
       │                 │
       │            Reconnect
       │                 │
       ▼                 ▼
  ┌──────────────────────────────┐
  │ pd.read_sql_query(sql)       │
  └──────────────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼────┐       ┌────▼────┐
   │ Success │       │ Error   │
   └────┬────┘       └────┬────┘
        │                 │
        ▼                 ▼
   DataFrame           String
   (results)           (error message)
```

#### Why Return String on Error?
- **Type safety**: Caller can check `isinstance(result, pd.DataFrame)`
- **User-friendly**: Error messages are displayed in UI
- **No exceptions**: Caller doesn't need try/except

---

### Method: `execute_sql(sql)` → bool

For non-SELECT statements (INSERT, UPDATE, DELETE, DDL).

```python
def execute_sql(self, sql: str) -> bool:
    try:
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()      # Commit transaction
        cursor.close()
        return True
    except Exception as e:
        self.conn.rollback()    # Rollback on error
        return False
```

#### Transaction Safety:
- **commit()**: Makes changes permanent
- **rollback()**: Undoes changes on error
- **cursor.close()**: Releases database resources

#### When Is This Used?
- Creating tables (DDL)
- Inserting data
- Updating/deleting records
- Currently not used in main app (read-only for safety)

---

### Method: `get_table_names()` → List[str]

Queries PostgreSQL's information_schema to discover tables.

```python
def get_table_names(self):
    sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    result = self.execute_query(sql)
    if isinstance(result, pd.DataFrame):
        return result['table_name'].tolist()
    return []
```

#### Why `table_schema = 'public'`?
- PostgreSQL has multiple schemas (pg_catalog, information_schema, public, etc.)
- `public` is the default schema where user tables live
- Filters out system tables

---

### Method: `get_table_schema(table_name)` → DataFrame

Gets column information for a specific table.

```python
def get_table_schema(self, table_name: str):
    sql = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """
    return self.execute_query(sql)
```

#### Return Example:
```
   column_name      data_type  is_nullable
0           id        integer           NO
1         date           date           NO
2       amount  numeric(10,2)           NO
3      product character varying       YES
4       region character varying       YES
```

#### Usage in Application:
- LLM context building (nl2sql_converter.py)
- Schema display in GUI
- Database introspection for intelligent SQL generation

---

### Method: `close()`

Properly closes the database connection.

```python
def close(self):
    if self.conn and not self.conn.closed:
        self.conn.close()
        log_db("Connection", "Database connection closed", success=True)
```

#### Why Check `not self.conn.closed`?
- Prevents "connection already closed" errors
- Allows calling close() multiple times safely
- Required for cleanup patterns

---

### Destructor: `__del__`

```python
def __del__(self):
    self.close()
```

#### Purpose:
- Automatic cleanup when object is garbage collected
- Ensures connections don't leak
- Called even if programmer forgets to call close()

---

## Usage in Application

### In main.py:
```python
db = DatabaseController()
if db.connect():
    tables = db.get_table_names()
    if 'sales' in tables:
        result = db.execute_query("SELECT * FROM sales LIMIT 5")
    db.close()
```

### In nl2sql_converter.py:
```python
# Get full database context for LLM
schema = db.execute_query("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'sales'
""")

# Execute LLM-generated SQL
sql, result, metadata = converter.convert_and_execute("total sales by region")
# result is a DataFrame if successful
```

---

## File Relationships

```
db_controller.py
    │
    ├──> imports from config.py (DB_CONFIG)
    │
    ├──> imports from src/utils/logger.py
    │
    ├──> used by main.py (startup checks)
    │
    ├──> used by src/llm/nl2sql_converter.py (schema introspection, query execution)
    │
    └──> used by tests/test_comprehensive.py (test execution)
```

---

## Connection Pooling Note

Current implementation creates a new connection per DatabaseController instance. For production with high load, consider:

```python
# Future enhancement: Connection pooling
from psycopg2 import pool
connection_pool = pool.SimpleConnectionPool(1, 20, ...)
conn = connection_pool.getconn()
# ... use connection ...
connection_pool.putconn(conn)
```

Current design is sufficient for single-user desktop application.

---

## Error Handling Summary

| Error Type | Method | Response |
|------------|--------|----------|
| Connection refused | connect() | Returns False |
| Auth failed | connect() | Returns False |
| Invalid SQL syntax | execute_query() | Returns error string |
| Runtime SQL error | execute_query() | Returns error string |
| Closed connection | execute_query() | Auto-reconnects |
| Commit failure | execute_sql() | Rollback + False |

---

## Logging

All database operations are logged:

| Log Level | Tag | Event |
|-----------|-----|-------|
| DEBUG | DB_INIT | Controller created |
| INFO | DB_CONNECT | Connection attempt |
| DEBUG | DB_QUERY | Query executing |
| INFO | DATABASE | Query results |
| WARNING | DB_QUERY | Reconnection needed |
| ERROR | DB_QUERY | Query failures |
