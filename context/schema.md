# schema.sql - Database Schema Definition

## File Location
```
nl2sql_assistant/src/database/schema.sql
```

## Purpose
This SQL file defines the complete database schema for the NL2SQL Voice Assistant. It:
- Creates the `sales` table structure
- Sets up performance indexes
- Inserts sample sales data (60 records)
- Provides verification queries

---

## How to Execute

### Option 1: Using pgAdmin
1. Open pgAdmin
2. Connect to PostgreSQL server
3. Select database `nl2sql_db`
4. Open Query Tool
5. Paste contents of schema.sql
6. Execute (F5)

### Option 2: Using psql command line
```bash
psql -U postgres -d nl2sql_db -f src/database/schema.sql
```

### Option 3: Using Python populate_db.py
```bash
python src/database/populate_db.py
```

---

## Schema Structure

### DROP Statement

```sql
DROP TABLE IF EXISTS sales CASCADE;
```

#### What It Does:
- Removes existing `sales` table if it exists
- `CASCADE` removes dependent objects (indexes, triggers, constraints)
- Ensures clean slate for recreation

#### Why This Design:
- Allows re-running schema.sql without errors
- Useful during development and testing
- **Warning**: Destroys all existing data!

---

### CREATE TABLE Statement

```sql
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    product VARCHAR(100),
    region VARCHAR(50),
    quantity INTEGER DEFAULT 1,
    customer_type VARCHAR(50) DEFAULT 'Regular'
);
```

#### Column Definitions:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| **id** | SERIAL | PRIMARY KEY | Auto-incrementing unique identifier |
| **date** | DATE | NOT NULL | Sale date (YYYY-MM-DD format) |
| **amount** | DECIMAL(10,2) | NOT NULL | Sale amount in Rupees (10 digits, 2 decimal) |
| **product** | VARCHAR(100) | - | Product name (up to 100 chars) |
| **region** | VARCHAR(50) | - | Sales region (North/South/East/West) |
| **quantity** | INTEGER | DEFAULT 1 | Number of units sold |
| **customer_type** | VARCHAR(50) | DEFAULT 'Regular' | Customer category |

#### Data Type Rationale:

| Type | Why This Choice |
|------|----------------|
| **SERIAL** | PostgreSQL auto-increment; simpler than identity columns |
| **DATE** | Stores date only (no time); efficient for daily aggregations |
| **DECIMAL(10,2)** | Exact precision for money; avoids floating-point errors |
| **VARCHAR(100)** | Variable length; saves space vs CHAR(100) |
| **INTEGER** | 4 bytes; sufficient for quantity (up to 2 billion) |

#### NOT NULL vs NULL Columns:

| Column | Nullable | Reason |
|--------|----------|--------|
| id, date, amount | NOT NULL | Core transaction data required |
| product, region | NULL | Allows flexibility for incomplete data |
| quantity, customer_type | NULL (with DEFAULT) | Optional but has sensible defaults |

---

### Index Definitions

```sql
CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_product ON sales(product);
CREATE INDEX idx_sales_region ON sales(region);
CREATE INDEX idx_sales_amount ON sales(amount);
```

#### What Are Indexes?
Indexes are data structures that speed up data retrieval at the cost of extra storage and slower writes.

#### Why These Indexes?

| Index | Common Query Pattern | Speed Improvement |
|-------|---------------------|-------------------|
| **idx_sales_date** | "January sales", "last month" | Fast date range queries |
| **idx_sales_product** | "laptop sales", "by product" | Fast product filtering |
| **idx_sales_region** | "north region", "by region" | Fast region filtering |
| **idx_sales_amount** | "sales > 1000", "top sales" | Fast amount comparisons |

#### Index Performance:

Without index: **O(n)** - scans all 60 rows
With index: **O(log n)** - binary search in B-tree

For 60 rows, difference is minimal. For 1 million rows, index is **critical**.

---

## Sample Data

### Data Distribution

The schema inserts **60 sales records** spanning:
- **Date range**: 2025-01-02 to 2025-03-31 (Q1 2025)
- **Products**: 10 different products
- **Regions**: 4 regions (equally distributed)
- **Customer types**: 3 categories

### Product Catalog

| Product | Price Range (Rs) | Category |
|---------|-----------------|----------|
| Laptop | 1299 - 2199 | High-end |
| Desktop | 749 - 1249 | Mid-range |
| Monitor | 299 - 549 | Accessories |
| Keyboard | 129 - 199 | Accessories |
| Mouse | 59 - 109 | Accessories |
| Headphones | 199 - 399 | Accessories |
| Webcam | 119 - 229 | Accessories |
| Tablet | 549 - 849 | Mobile |
| Smartphone | 899 - 1499 | Mobile |
| Router | 89 - 199 | Networking |

### Region Distribution

| Region | Count | Percentage |
|--------|-------|------------|
| North | 15 | 25% |
| South | 15 | 25% |
| East | 15 | 25% |
| West | 15 | 25% |

### Customer Type Distribution

| Type | Count | Description |
|------|-------|-------------|
| Regular | 20 | Standard consumers |
| Business | 20 | B2B customers |
| Premium | 20 | High-value customers |

### Monthly Distribution

| Month | Count | Description |
|-------|-------|-------------|
| January 2025 | 20 | First month |
| February 2025 | 18 | Second month |
| March 2025 | 22 | Third month |

---

## INSERT Statement Structure

```sql
INSERT INTO sales (date, amount, product, region, quantity, customer_type) VALUES
('2025-01-02', 1299.99, 'Laptop', 'North', 1, 'Business'),
('2025-01-03', 899.50, 'Desktop', 'South', 1, 'Regular'),
...
('2025-03-31', 199.99, 'Router', 'West', 3, 'Premium');
```

#### Data Pattern:
- Each row represents one sale transaction
- Dates are sequential but not consecutive (realistic gaps)
- Amounts vary within product price ranges
- Even distribution across regions and customer types

---

## Verification Queries

The schema includes three verification queries at the end:

### Query 1: Total Row Count
```sql
SELECT COUNT(*) as total_rows FROM sales;
```
Expected output: `60`

### Query 2: Product Revenue Summary
```sql
SELECT product, COUNT(*) as count, SUM(amount) as total_revenue 
FROM sales 
GROUP BY product 
ORDER BY total_revenue DESC;
```

Expected output (example):
```
   product    | count | total_revenue
--------------+-------+---------------
 Laptop       |     6 |      10099.93
 Smartphone   |     6 |       6899.94
 Desktop      |     6 |       5849.94
 ...
```

### Query 3: Region Summary
```sql
SELECT region, COUNT(*) as count, SUM(amount) as total_revenue 
FROM sales 
GROUP BY region 
ORDER BY total_revenue DESC;
```

Expected output (example):
```
  region | count | total_revenue
---------+-------+---------------
 East    |    15 |      12099.87
 North   |    15 |      11699.88
 ...
```

---

## Usage in Application

### Referenced by nl2sql_converter.py:
The schema structure is introspected at runtime:
```python
schema = db.execute_query("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'sales'
""")
```

### Referenced by rag_indexer.py:
Schema documentation is loaded from `data/schema_docs.txt` which describes this table.

### Referenced by LLM prompts:
Column names and types are passed to Qwen for SQL generation.

---

## File Relationships

```
schema.sql
    │
    ├──> Creates: PostgreSQL 'sales' table
    │
    ├──> Alternative: src/database/populate_db.py (Python version)
    │
    ├──> Documented in: data/schema_docs.txt
    │
    └──> Introspected by: src/llm/nl2sql_converter.py
```

---

## Design Decisions & Rationale

| Decision | Why |
|----------|-----|
| SERIAL for id | Simpler than UUID, sufficient for demo |
| DATE not TIMESTAMP | Demo data is daily granularity |
| DECIMAL for money | Exact arithmetic, no float errors |
| 4 indexes | Cover common WHERE clauses |
| 60 records | Enough for all test cases, fast queries |
| Even distribution | Predictable results for testing |
| Q1 2025 dates | Recent, realistic date range |
