# rag_indexer.py - RAG Context Retrieval Module

## File Location
```
nl2sql_assistant/src/llm/rag_indexer.py
```

## Purpose
This module provides **Retrieval-Augmented Generation (RAG)** functionality using a simple keyword-based search. It:
- Loads schema documentation from text file
- Retrieves relevant context for queries
- Enhances LLM prompts with domain knowledge

---

## What is RAG?

**RAG = Retrieval-Augmented Generation**

Instead of relying solely on the LLM's training data, RAG:
1. **Retrieves** relevant documents from a knowledge base
2. **Augments** the LLM prompt with this context
3. **Generates** more accurate responses

```
Traditional LLM:
User Query ──────────────────────> LLM ──> SQL

RAG-Enhanced LLM:
User Query ──> RAG Search ──> Relevant Docs ──> LLM ──> Better SQL
                    │
                    └── data/schema_docs.txt
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 RAGIndexer                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │        data/schema_docs.txt             │   │
│  │                                         │   │
│  │  "Table: sales"                         │   │
│  │  "Columns: id, date, amount..."         │   │
│  │  "Product Values: Laptop, Desktop..."   │   │
│  │  "Common SQL Patterns: SELECT SUM..."   │   │
│  └────────────────┬────────────────────────┘   │
│                   │                             │
│                   ▼                             │
│  ┌─────────────────────────────────────────┐   │
│  │      Keyword-Based Search               │   │
│  │      - Word intersection matching       │   │
│  │      - SQL keyword boosting             │   │
│  │      - Exact phrase matching            │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Dependencies

```python
import os, sys
from pathlib import Path
from typing import List, Optional
from src.utils.logger import logger
```

### Why No Vector Embeddings?
This implementation uses **keyword matching** instead of semantic embeddings because:
- Simpler, fewer dependencies
- No ML models required
- Fast startup time
- Sufficient for controlled domain (SQL/database)
- Avoids FAISS/sentence-transformers complexity

---

## Class: RAGIndexer

### Constructor

```python
def __init__(self, schema_file: str = "data/schema_docs.txt"):
    self.schema_file = schema_file
    self.documents = []      # List of text chunks
    self.enabled = False
    
    if self._load_schema():
        self.enabled = True
```

---

### Method: `_load_schema()`

Loads and splits the schema documentation into searchable chunks.

```python
def _load_schema(self) -> bool:
    with open(self.schema_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split on double newlines into paragraphs
    self.documents = [doc.strip() for doc in content.split('\n\n') if doc.strip()]
```

#### Document Splitting:
The schema_docs.txt is split on blank lines (`\n\n`), creating individual chunks:

```
Chunk 1: "Table: sales\nDescription: Sales transaction records..."
Chunk 2: "Columns:\n- id: INTEGER (Primary Key)..."
Chunk 3: "Product Values (10 types):\n- Laptop..."
Chunk 4: "Common SQL Query Patterns:\n1. Total Sales..."
...
```

---

### Method: `search()` - The Core Algorithm

```python
def search(self, query: str, k: int = 5) -> List[str]:
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    scored_docs = []
    for doc in self.documents:
        doc_lower = doc.lower()
        doc_words = set(doc_lower.split())
        
        # Score 1: Word intersection
        matches = len(query_words & doc_words)
        
        # Score 2: Exact phrase match (bonus +10)
        if query_lower in doc_lower:
            matches += 10
        
        # Score 3: SQL keyword boost (+2 each)
        for term in ['select', 'sum', 'count', 'avg', 'group', 'where', 'order']:
            if term in query_lower and term in doc_lower:
                matches += 2
        
        if matches > 0:
            scored_docs.append((matches, doc))
    
    # Sort by score, return top k
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored_docs[:k]]
```

#### Scoring Algorithm Breakdown:

| Factor | Score | Example |
|--------|-------|---------|
| **Word intersection** | +1 per word | "sales region" matches doc with "sales" and "region" = +2 |
| **Exact phrase match** | +10 | Query "total sales" in doc = +10 |
| **SQL keyword boost** | +2 per term | Query has "sum", doc has "SUM" = +2 |

#### Example Scoring:

Query: `"total sales by region"`

| Document | Word Match | Phrase | SQL Keywords | Total Score |
|----------|------------|--------|--------------|-------------|
| "Total Sales: SELECT SUM..." | 2 | +10 | +2 (sum) | 14 |
| "Sales by Region: SELECT..." | 3 | +10 | +2 (select) | 15 |
| "Product Values: Laptop..." | 0 | 0 | 0 | 0 |

**Winner**: "Sales by Region" chunk (15 points)

---

### Method: `get_context()`

Returns formatted context string for LLM prompts.

```python
def get_context(self, query: str, k: int = 5) -> str:
    if not self.enabled:
        return self._get_full_context()  # Fallback
    
    results = self.search(query, k)
    
    if results:
        context = "\n\n".join(results)
        logger.d("RAG_SEARCH", f"Found {len(results)} relevant sections")
        return context
    
    return self._get_full_context()  # Fallback if no matches
```

---

### Method: `_get_full_context()`

Fallback when search fails - returns hardcoded schema.

```python
def _get_full_context(self) -> str:
    if self.documents:
        return "\n\n".join(self.documents[:10])
    
    return """Database Schema:
Table: sales
Columns: 
- id (INTEGER, Primary Key)
- date (DATE, format YYYY-MM-DD)
- amount (DECIMAL, sales amount in Rs)
- product (VARCHAR: Laptop, Desktop, Monitor...)
- region (VARCHAR: North, South, East, West)
- quantity (INTEGER, units sold)
- customer_type (VARCHAR: Regular, Business, Premium)

Common Patterns:
- Total: SELECT SUM(amount) FROM sales
- By product: SELECT product, SUM(amount) FROM sales GROUP BY product
- By region: SELECT region, SUM(amount) FROM sales GROUP BY region"""
```

---

## Input File: data/schema_docs.txt

The RAG system reads from this file:

```
Table: sales
Description: Sales transaction records for technology products

Columns:
- id: INTEGER (Primary Key, auto-increment)
- date: DATE (format: YYYY-MM-DD, range: 2025-01-01 to 2025-03-31)
- amount: DECIMAL(10,2) (sales amount in Rs)
- product: VARCHAR(100) (product name)
- region: VARCHAR(50) (sales region)
- quantity: INTEGER (units sold)
- customer_type: VARCHAR(50) (customer category)

Product Values (10 types):
- Laptop (high-end: Rs 1299-2199)
- Desktop (mid-range: Rs 749-1249)
...

Region Values (4 regions):
- North
- South
- East
- West

Common SQL Query Patterns:

1. Total Sales:
   SELECT SUM(amount) as total_sales FROM sales;

2. Sales by Product:
   SELECT product, SUM(amount) as total_revenue
   FROM sales GROUP BY product ORDER BY total_revenue DESC;
...
```

---

## Usage in Application

### In nl2sql_converter.py:

```python
from src.llm.rag_indexer import RAGIndexer

rag = RAGIndexer()

# Get context for user query
context = rag.get_context("show total sales by region", k=5)

# Add to LLM prompt
full_prompt = f"""
{database_context}

ADDITIONAL DOMAIN CONTEXT:
{context}

USER QUESTION: show total sales by region
"""
```

---

## File Relationships

```
rag_indexer.py
    │
    ├──> reads from data/schema_docs.txt
    │
    ├──> used by src/llm/nl2sql_converter.py
    │
    └──> imports from src/utils/logger.py
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Load time | ~10ms | Simple text file read |
| Search time | ~1ms | Keyword matching is fast |
| Memory usage | ~10KB | Just text in memory |
| Chunks loaded | 16 | Default schema_docs.txt |

---

## Comparison: Keyword vs Vector Search

| Aspect | Keyword (Current) | Vector (Alternative) |
|--------|-------------------|----------------------|
| **Accuracy** | Good for known terms | Better for semantics |
| **Speed** | ~1ms | ~50ms |
| **Dependencies** | None | FAISS, transformers |
| **Memory** | ~10KB | ~500MB |
| **Startup** | Instant | 5-10 seconds |
| **Best for** | Controlled domain | Open-ended queries |

**Our choice**: Keyword search is sufficient because:
- Limited domain (SQL queries)
- Known vocabulary (column names, SQL keywords)
- Speed is important for UX
- Minimal dependencies

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Keyword matching | Simple, fast, no ML deps |
| Double newline split | Natural paragraph breaks |
| SQL keyword boost | Prioritizes relevant patterns |
| Phrase match bonus | Exact matches are valuable |
| Fixed schema file | Single source of truth |
| Fallback context | Always returns something |
