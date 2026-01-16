# nl2sql_converter.py - Natural Language to SQL Converter

## File Location
```
nl2sql_assistant/src/llm/nl2sql_converter.py
```

## Purpose
This is the **central orchestration module** that ties together all NL2SQL components:
- Database context extraction
- RAG-enhanced prompting
- LLM SQL generation
- Query execution
- Self-verification with automatic retry

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     nl2sql_converter.py                          │
│                      (NL2SQLConverter)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │  RAG Indexer   │  │ QwenSQLGen    │  │ DatabaseController │ │
│  │  (Context)     │  │ (LLM)         │  │ (Execution)        │ │
│  │                │  │               │  │                    │ │
│  │ - Schema docs  │  │ - Generate SQL│  │ - Connect          │ │
│  │ - Query hints  │  │ - Verify SQL  │  │ - Execute          │ │
│  └───────┬────────┘  └───────┬───────┘  └─────────┬──────────┘ │
│          │                   │                     │            │
│          └───────────────────┼─────────────────────┘            │
│                              │                                  │
│                    convert_and_execute()                        │
│                              │                                  │
│                              ▼                                  │
│              ┌───────────────────────────────────┐              │
│              │ User: "show total sales by region" │              │
│              └───────────────┬───────────────────┘              │
│                              │                                  │
│              ┌───────────────▼───────────────────┐              │
│              │ SQL: SELECT region, SUM(amount)   │              │
│              │      FROM sales GROUP BY region   │              │
│              └───────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Dependencies

```python
from src.llm.rag_indexer import RAGIndexer           # Context retrieval
from src.llm.llm_generator import QwenSQLGenerator   # SQL generation
from src.database.db_controller import DatabaseController  # Execution
from src.utils.logger import logger
import pandas as pd
```

---

## Class: NL2SQLConverter

### Constants

```python
MAX_RETRIES = 5  # Maximum attempts to generate correct SQL
```

#### Why 5 Retries?
- Complex queries may need multiple attempts
- Each retry includes error feedback
- Diminishing returns after 5 attempts
- Prevents infinite loops

---

### Constructor: `__init__()`

```python
def __init__(self):
    self.enabled = False
    self.rag = None            # RAG context
    self.llm = None            # LLM generator
    self.db = None             # Database controller
    self._db_context_cache = None   # Cached context
    self._db_stats_cache = None     # Cached statistics
```

#### Initialization Sequence:

```
┌─────────────────────────────────────┐
│ 1. Initialize RAG Indexer           │
│    Load schema_docs.txt             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 2. Initialize Ollama LLM            │
│    Connect to Qwen2.5-Coder         │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 3. Initialize Database Controller   │
│    Ready for connections            │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 4. Set enabled = True               │
│    If LLM + DB both ready           │
└─────────────────────────────────────┘
```

---

### Method: `get_gpu_memory_usage()`

Returns current GPU memory utilization.

```python
def get_gpu_memory_usage(self) -> Optional[Dict[str, float]]:
    result = subprocess.run(
        ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=5
    )
    # Returns: {"allocated": 4.5, "total": 16.0}  # in GB
```

#### Used By:
- Main window GUI for memory display
- Performance monitoring

---

### Method: `_get_full_database_context()`

The **most important method** - builds rich context for the LLM.

```python
def _get_full_database_context(self) -> Tuple[str, Dict[str, Any]]:
```

#### What It Extracts:

1. **Table Schema**:
   ```sql
   SELECT column_name, data_type, is_nullable
   FROM information_schema.columns
   ```

2. **Sample Data** (10 rows):
   ```sql
   SELECT * FROM {table} LIMIT 10
   ```

3. **Total Row Count**:
   ```sql
   SELECT COUNT(*) FROM {table}
   ```

4. **Unique Values** (for VARCHAR columns):
   ```sql
   SELECT DISTINCT {col} FROM {table} LIMIT 20
   ```

5. **Date Range Analysis** (for DATE columns):
   ```sql
   SELECT MIN(date), MAX(date), 
          COUNT(DISTINCT EXTRACT(YEAR FROM date)),
          COUNT(DISTINCT EXTRACT(MONTH FROM date))
   ```

#### Example Output Context:

```
=== TABLE: sales ===
COLUMNS:
  - id: integer (NOT NULL)
  - date: date (NOT NULL)
  - amount: numeric (NOT NULL)
  - product: character varying (NULL)
  - region: character varying (NULL)
  - quantity: integer (NULL)
  - customer_type: character varying (NULL)

SAMPLE DATA (first 10 rows):
id | date       | amount  | product    | region | quantity | customer_type
1  | 2025-01-02 | 1299.99 | Laptop     | North  | 1        | Business
...

TOTAL ROWS IN TABLE: 60
UNIQUE VALUES in 'product': ['Desktop', 'Headphones', 'Keyboard', ...]
UNIQUE VALUES in 'region': ['East', 'North', 'South', 'West']
UNIQUE VALUES in 'customer_type': ['Business', 'Premium', 'Regular']

DATE RANGE in 'date': 2025-01-02 to 2025-03-31
AVAILABLE YEARS in 'date': [2025]
AVAILABLE MONTHS with data: ['January 2025 (20 rows)', 'February 2025 (18 rows)', 'March 2025 (22 rows)']
```

#### Why This Context?
| Information | Why It Helps LLM |
|-------------|------------------|
| Column types | Correct function usage (SUM on numbers) |
| Sample data | Understands data format |
| Unique values | Exact spelling for WHERE clauses |
| Date range | Knows which dates exist |
| Row counts | Validates expected results |

---

### Method: `convert()`

Simple wrapper that returns only the SQL.

```python
def convert(self, nl_query: str) -> str:
    sql, _, _ = self.convert_and_execute(nl_query, execute=False)
    return sql
```

---

### Method: `convert_and_execute()` ⭐ CORE METHOD

The main pipeline that converts natural language to SQL with automatic retry.

```python
def convert_and_execute(
    self, 
    nl_query: str,
    execute: bool = True
) -> Tuple[str, Optional[pd.DataFrame], Dict[str, Any]]:
```

#### Return Values:

| Return | Type | Description |
|--------|------|-------------|
| sql | str | Generated SQL query |
| result | DataFrame or None | Query results |
| metadata | Dict | Attempt history, status |

#### Flow Diagram:

```
┌─────────────────────────────────────┐
│ User Query: "show south sales"      │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 1. Get Database Context             │
│    - Schema, samples, unique values │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 2. Add RAG Context                  │
│    - Relevant schema docs           │
└────────────────┬────────────────────┘
                 │
    ┌────────────┴───────────────────────┐
    │         RETRY LOOP (max 5)          │
    │┌────────────────────────────────────┴┐
    ││                                     │
    ││  3. LLM Generates SQL               │
    ││     llm.generate_sql(query, ctx)    │
    ││                 │                   │
    ││                 ▼                   │
    ││  4. Execute Query                   │
    ││     db.execute_query(sql)          │
    ││                 │                   │
    ││        ┌───────┴───────┐           │
    ││        │               │           │
    ││    ┌───▼───┐      ┌────▼────┐      │
    ││    │ Error │      │ Success │      │
    ││    └───┬───┘      └────┬────┘      │
    ││        │               │           │
    ││        ▼               ▼           │
    ││  Retry with       5. Verify Result │
    ││  error feedback      llm.verify()  │
    ││                        │           │
    ││               ┌────────┴────────┐  │
    ││               │                 │  │
    ││          ┌────▼────┐      ┌────▼───┐
    ││          │ CORRECT │      │INCORRECT│
    ││          └────┬────┘      └────┬───┘
    ││               │                │    │
    ││               ▼           Retry with│
    ││           RETURN         fix feedback
    └┴────────────────────────────────────┘
```

#### Retry Mechanism:

Each retry includes **feedback from the previous attempt**:

```python
current_query = f"""Original question: {nl_query}

Previous SQL was INCORRECT:
SQL: {sql}
Result: {len(result)} rows returned
Problem: {verification.get('reason')}
Suggested fix: {verification.get('suggested_fix')}

IMPORTANT: 
- If question asks for specific category, result should ONLY contain that
- If question asks for "all" data, do NOT use LIMIT
- Use exact column values from database context

Generate a CORRECTED SQL query:"""
```

#### Metadata Structure:

```python
metadata = {
    "attempts": 3,              # How many tries
    "original_query": "...",    # User's input
    "final_status": "verified_correct",  # or "max_retries_reached"
    "verification_history": [
        {"attempt": 1, "sql": "...", "is_correct": False, "reason": "..."},
        {"attempt": 2, "sql": "...", "is_correct": False, "reason": "..."},
        {"attempt": 3, "sql": "...", "is_correct": True, "reason": "..."}
    ]
}
```

---

### Method: `get_suggestions()`

Dynamic query suggestions based on database content.

```python
def get_suggestions(self, partial_query: str = "") -> List[str]:
    suggestions = [
        "Show all data",
        "Total sales by region",
        "Top 10 products by revenue",
        ...
    ]
    
    # Add suggestions from unique values
    for table, stats in db_stats.items():
        for col, values in stats["unique_values"].items():
            for val in values[:3]:
                suggestions.append(f"Show {val.lower()} {table}")
```

#### Example Output:
```python
[
    "Show all data",
    "Total sales by region",
    "Show north sales",      # Dynamic from data
    "Show south sales",      # Dynamic from data
    "Show laptop sales",     # Dynamic from data
]
```

---

## Usage in Application

### In main_window.py:

```python
converter = NL2SQLConverter()

# When user submits query
sql, result, metadata = converter.convert_and_execute(
    "show total sales by region"
)

if isinstance(result, pd.DataFrame):
    # Display in table
    display_dataframe(result)
else:
    # Show error
    show_error(metadata.get("error"))
```

---

## File Relationships

```
nl2sql_converter.py
    │
    ├──> imports from src/llm/rag_indexer.py (context)
    │
    ├──> imports from src/llm/llm_generator.py (SQL generation)
    │
    ├──> imports from src/database/db_controller.py (execution)
    │
    ├──> used by src/gui/main_window.py (GUI integration)
    │
    └──> used by tests/test_comprehensive.py (testing)
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| First query | ~8-10 seconds | Context building + LLM |
| Subsequent queries | ~6-8 seconds | Context cached |
| With retries | +6 seconds per retry | Each retry is full LLM call |
| Context caching | Saves ~2 seconds | Reuses schema info |

---

## Error Recovery

| Scenario | Recovery |
|----------|----------|
| SQL syntax error | Retry with error message |
| Wrong columns | Retry with schema reminder |
| Verification fail | Retry with fix suggestion |
| Max retries | Return last SQL + result |
| DB connection fail | Return SQL only |

---

## Design Decisions

| Decision | Why |
|----------|-----|
| 5 max retries | Balance between accuracy and speed |
| Context caching | Avoid repeated DB introspection |
| Rich context | LLM needs full information |
| Self-verification | Catches errors before user sees |
| Error feedback | Each retry gets smarter |
| Fallback output | Always returns something usable |
