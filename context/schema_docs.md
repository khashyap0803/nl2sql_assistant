# schema_docs.txt - RAG Schema Documentation

## File Location
```
nl2sql_assistant/data/schema_docs.txt
```

## Purpose
This text file provides **domain knowledge** for the RAG system. It:
- Documents the database schema
- Provides sample SQL patterns
- Helps the LLM generate accurate queries
- Contains business context

---

## How It's Used

The RAG indexer loads this file and splits it into searchable chunks:

```
schema_docs.txt
    │
    ├──> RAGIndexer._load_schema()
    │        Splits on blank lines (\n\n)
    │
    ├──> RAGIndexer.search(query)
    │        Keyword matching
    │
    └──> Added to LLM prompt as context
```

---

## Content Structure

### Section 1: Table Overview
```
Table: sales
Description: Sales transaction records for technology products
```

### Section 2: Column Definitions
```
Columns:
- id: INTEGER (Primary Key, auto-increment)
- date: DATE (format: YYYY-MM-DD)
- amount: DECIMAL(10,2) (sales amount in Rs)
- product: VARCHAR(100) (product name)
- region: VARCHAR(50) (sales region)
- quantity: INTEGER (units sold)
- customer_type: VARCHAR(50) (customer category)
```

### Section 3: Valid Values
```
Product Values (10 types):
- Laptop (high-end: Rs 1299-2199)
- Desktop (mid-range: Rs 749-1249)
- Monitor (accessory: Rs 299-549)
...

Region Values (4 regions):
- North
- South
- East
- West

Customer Types (3 categories):
- Regular (standard consumers)
- Business (B2B customers)
- Premium (high-value customers)
```

### Section 4: SQL Patterns
```
Common SQL Query Patterns:

1. Total Sales:
   SELECT SUM(amount) as total_sales FROM sales;

2. Sales by Product:
   SELECT product, SUM(amount) as total_revenue
   FROM sales GROUP BY product ORDER BY total_revenue DESC;

3. Regional Analysis:
   SELECT region, COUNT(*) as num_sales, SUM(amount) as revenue
   FROM sales GROUP BY region;

4. Date Filtering:
   SELECT * FROM sales WHERE date BETWEEN '2025-01-01' AND '2025-01-31';
   SELECT * FROM sales WHERE EXTRACT(MONTH FROM date) = 1;

5. Top N Results:
   SELECT * FROM sales ORDER BY amount DESC LIMIT 10;
```

---

## Why This Format?

| Choice | Reason |
|--------|--------|
| Plain text | Simple, no parsing needed |
| Blank line separators | Easy to split into chunks |
| Real SQL examples | LLM can copy patterns |
| Price ranges | Business context |
| Multiple patterns | Cover common use cases |

---

## File Relationships

```
schema_docs.txt
    │
    ├──> Read by: src/llm/rag_indexer.py
    │
    ├──> Documents: src/database/schema.sql
    │
    └──> Enhances: LLM prompts via nl2sql_converter.py
```
