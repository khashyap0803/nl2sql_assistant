# test_comprehensive.py - Comprehensive Test Suite

## File Location
```
nl2sql_assistant/tests/test_comprehensive.py
```

## Purpose
This is the **main test suite** for the NL2SQL Voice Assistant, containing 100 test cases that validate SQL generation accuracy across different complexity levels.

---

## Test Structure

```
┌──────────────────────────────────────────────────────────────────┐
│                  100 Test Cases                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Simple     │  │   Medium     │  │   Complex    │           │
│  │  (10 tests)  │  │  (20 tests)  │  │  (20 tests)  │           │
│  │              │  │              │  │              │           │
│  │ "all"        │  │ "total..."   │  │ "monthly..." │           │
│  │ "north"      │  │ "average..." │  │ "quarterly"  │           │
│  │ "south"      │  │ "top 10..."  │  │ "week..."    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Highly Complex                           │ │
│  │                     (50 tests)                              │ │
│  │                                                             │ │
│  │ "show products in top 10 by revenue that sold in all..."   │ │
│  │ "calculate year over year growth rate..."                  │ │
│  │ "find products with statistically significant..."          │ │
│  │ "calculate the geometric mean of sales amounts"            │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## How to Run

```bash
python tests/test_comprehensive.py
```

---

## Test Case Structure

Each test case is a dictionary with:

```python
{
    "id": 1,                           # Unique test ID
    "query": "all",                    # Natural language query
    "complexity": "simple",            # Category
    "description": "Get all records",  # What it tests
    "expected_keywords": ["SELECT", "FROM"],  # Required SQL keywords
    "expected_min_rows": 50,           # Minimum rows expected
    "expected_max_rows": 70            # Maximum rows expected
}
```

---

## Complexity Levels

### Simple (10 tests)
Basic queries with single conditions:

| ID | Query | Expected |
|----|-------|----------|
| 1 | "all" | SELECT * FROM sales |
| 2 | "show all north region sales" | WHERE region = 'North' |
| 3 | "show all south sales" | WHERE region = 'South' |
| 4 | "show all east region data" | WHERE region = 'East' |
| 5 | "show all west sales" | WHERE region = 'West' |
| 6 | "show all laptop sales" | WHERE product = 'Laptop' |
| ... | ... | ... |

### Medium (20 tests)
Queries with aggregations and sorting:

| ID | Query | Expected |
|----|-------|----------|
| 11 | "total sales" | SUM(amount) |
| 12 | "average amount" | AVG(amount) |
| 13 | "total sales by region" | GROUP BY region |
| 17 | "top 10 highest sales" | ORDER BY ... LIMIT 10 |
| ... | ... | ... |

### Complex (20 tests)
Multi-condition and time-based queries:

| ID | Query | Expected |
|----|-------|----------|
| 41 | "sales over 1000" | WHERE amount > 1000 |
| 44 | "monthly sales summary" | GROUP BY month |
| 45 | "quarterly sales" | QUARTER |
| 49 | "march sales data" | EXTRACT(MONTH) = 3 |
| ... | ... | ... |

### Highly Complex (50 tests)
Advanced SQL patterns:

| ID | Query | Expected |
|----|-------|----------|
| 61 | "show products that sold in both north and south" | INTERSECT or complex JOIN |
| 68 | "calculate the rolling 3-day average" | Window functions |
| 72 | "year over year growth rate" | LAG() function |
| 97 | "z-score normalized sales" | STDDEV, complex CTEs |
| 99 | "geometric mean of sales" | EXP(AVG(LN())) |
| 100 | "complete sales analysis report" | Multi-dimensional grouping |

---

## Validation Logic

```python
def validate_result(test_case, sql, result):
    # Check 1: SQL contains expected keywords
    for keyword in test_case.get("expected_keywords", []):
        if keyword.upper() not in sql.upper():
            return False, f"Missing: {keyword}"
    
    # Check 2: Row count within expected range
    if isinstance(result, pd.DataFrame):
        row_count = len(result)
        min_rows = test_case.get("expected_min_rows", 0)
        max_rows = test_case.get("expected_max_rows", float('inf'))
        
        if not (min_rows <= row_count <= max_rows):
            return False, f"Rows: {row_count}, expected {min_rows}-{max_rows}"
    
    return True, "Pass"
```

---

## Output Format

```
================================================================================
NL2SQL COMPREHENSIVE TEST SUITE - 100 TEST CASES
================================================================================

Initializing NL2SQL Converter...
[OK] Connected to database: nl2sql_db
[OK] Setup complete

Running 100 test cases...

--------------------------------------------------------------------------------
Test   1 [simple         ]: all                                               ... [PASS] (60 rows, 6.55s)
Test   2 [simple         ]: show all north region sales                       ... [PASS] (15 rows, 6.34s)
Test   3 [simple         ]: show all south sales                              ... [PASS] (15 rows, 6.07s)
...
Test  99 [highly_complex ]: calculate the geometric mean of sales amounts     ... [PASS] (1 rows, 5.99s)
Test 100 [highly_complex ]: show the complete sales analysis report           ... [PASS] (59 rows, 8.42s)
--------------------------------------------------------------------------------

================================================================================
TEST SUMMARY
================================================================================

OVERALL: 99/100 passed (99.0%)
  Passed: 99
  Failed: 0
  Errors: 1

BY COMPLEXITY:
  simple         :  10/ 10 (100.0%)
  medium         :  19/ 20 (95.0%)
  complex        :  20/ 20 (100.0%)
  highly_complex :  50/ 50 (100.0%)

================================================================================

Detailed results saved to: test_results.json
```

---

## Results File: test_results.json

Each test result is saved with:

```json
{
  "timestamp": "2026-01-16T11:59:09.036928",
  "summary": {
    "total": 100,
    "passed": 99,
    "failed": 0,
    "errors": 1,
    "by_complexity": {
      "simple": {"total": 10, "passed": 10},
      "medium": {"total": 20, "passed": 19},
      "complex": {"total": 20, "passed": 20},
      "highly_complex": {"total": 50, "passed": 50}
    }
  },
  "tests": [
    {
      "id": 1,
      "query": "all",
      "complexity": "simple",
      "passed": true,
      "sql": "SELECT * FROM sales;",
      "rows": 60,
      "time_taken": 8.02,
      "error": null
    },
    ...
  ]
}
```

---

## File Relationships

```
test_comprehensive.py
    │
    ├──> Uses: src/llm/nl2sql_converter.py
    │
    ├──> Uses: src/database/db_controller.py
    │
    ├──> Creates: test_results.json
    │
    └──> Imports from: src/utils/logger.py
```

---

## Test Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Coverage** | 100 tests across all complexity levels |
| **Reproducibility** | Deterministic test cases |
| **Flexibility** | Row count ranges, not exact values |
| **LLM-Aware** | Keywords checked, not exact SQL |
| **Realistic** | Real-world query patterns |
