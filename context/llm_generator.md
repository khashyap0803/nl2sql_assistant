# llm_generator.py - LLM SQL Generation Module

## File Location
```
nl2sql_assistant/src/llm/llm_generator.py
```

## Purpose
This module provides the core AI-powered SQL generation using Ollama's Qwen2.5-Coder model. It handles:
- Connection to local Ollama server
- Prompt engineering for accurate SQL generation
- SQL extraction from LLM responses
- Result verification through LLM self-checking

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     llm_generator.py                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐│
│  │  OllamaClient   │    │     QwenSQLGenerator            ││
│  │                 │    │                                 ││
│  │ - HTTP Client   │◄───│ - SQL Generation                ││
│  │ - /api/generate │    │ - Result Verification           ││
│  │ - /api/tags     │    │ - Prompt Engineering            ││
│  │ - /api/pull     │    │                                 ││
│  └─────────────────┘    └─────────────────────────────────┘│
│           ▲                          │                      │
│           │                          ▼                      │
│  ┌────────┴────────────────────────────────────────────────┤
│  │                  Ollama Server (localhost:11434)         │
│  │                  qwen2.5-coder:7b-instruct-q4_K_M       │
│  └──────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

---

## Dependencies

```python
import os, sys, re, json      # Standard library
import requests               # HTTP client for Ollama API
from typing import Optional, Dict, Any, Tuple
import pandas as pd           # DataFrame for result verification

from src.utils.logger import logger
```

### Why requests Instead of Ollama Python SDK?
- Simpler, fewer dependencies
- Direct control over HTTP calls
- SDK is a wrapper anyway
- Easier to debug/troubleshoot

---

## Global Constants

```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b-instruct-q4_K_M"
```

### Why These Values?
| Constant | Value | Reason |
|----------|-------|--------|
| **URL** | localhost:11434 | Ollama default port |
| **Model** | qwen2.5-coder:7b-instruct-q4_K_M | Best SQL accuracy on consumer GPU |

### Model Name Breakdown:
- **qwen2.5**: Alibaba's Qwen model, version 2.5
- **coder**: Fine-tuned for code generation (including SQL)
- **7b**: 7 billion parameters (good balance)
- **instruct**: Follows instructions well
- **q4_K_M**: 4-bit quantization, ~4GB VRAM

---

## Class: OllamaClient

A lightweight HTTP client for Ollama's REST API.

### Constructor

```python
def __init__(self, base_url: str = OLLAMA_BASE_URL):
    self.base_url = base_url
    self.available = False
    self._check_connection()
```

### Method: `_check_connection()`

```python
def _check_connection(self):
    try:
        response = requests.get(f"{self.base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            self.available = True
    except requests.exceptions.ConnectionError:
        logger.e("OLLAMA", "Cannot connect to Ollama - run: ollama serve")
```

#### What It Does:
1. Calls `/api/tags` endpoint (lists available models)
2. Sets `self.available = True` if successful
3. Logs error messages if Ollama is unreachable

#### Common Failure Scenarios:

| Scenario | Error | Solution |
|----------|-------|----------|
| Ollama not running | ConnectionError | Run `ollama serve` |
| Wrong port | Connection refused | Check OLLAMA_BASE_URL |
| Firewall blocked | Timeout | Allow localhost:11434 |

---

### Method: `generate()`

The core LLM inference method.

```python
def generate(
    self, 
    prompt: str, 
    model: str = OLLAMA_MODEL,
    system: str = None,
    temperature: float = 0.1
) -> Optional[str]:
```

#### Parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| **prompt** | str | The user prompt with database context |
| **model** | str | Model name (default: qwen2.5-coder) |
| **system** | str | System prompt for LLM behavior |
| **temperature** | float | Randomness (0.0-2.0, lower = more deterministic) |

#### Why temperature = 0.1?
- SQL must be **exact and consistent**
- Higher temperature = creative = wrong SQL
- 0.1 allows minimal variation for edge cases

#### API Payload:

```python
payload = {
    "model": model,
    "prompt": prompt,
    "stream": False,           # Get complete response at once
    "options": {
        "temperature": temperature,
        "num_predict": 1024    # Max tokens in response
    }
}
if system:
    payload["system"] = system  # Add system prompt
```

#### Why `stream: False`?
- Easier to process complete response
- No need for real-time display
- Simpler error handling

---

### Method: `list_models()`

Returns all locally available Ollama models.

```python
def list_models(self) -> list:
    response = requests.get(f"{self.base_url}/api/tags")
    return [m["name"] for m in data.get("models", [])]
```

---

## Class: QwenSQLGenerator

The main SQL generation class with intelligent prompt engineering.

### Constructor

```python
def __init__(self, model_name: str = OLLAMA_MODEL):
    self.model_name = model_name
    self.client = OllamaClient()
    self.enabled = False
    
    # Check if model exists, pull if needed
    available_models = self.client.list_models()
    model_found = any(model_name in m for m in available_models)
    
    if not model_found:
        self._pull_model(model_name)  # Auto-download
```

#### Auto-Download Feature:
If the required model isn't installed, it's automatically pulled from Ollama's registry.

---

### Method: `generate_sql()`

The main SQL generation method with sophisticated prompt engineering.

```python
def generate_sql(
    self,
    nl_query: str,
    db_context: str
) -> Optional[str]:
```

#### The System Prompt (Critical)

This is the "brain" of the SQL generation:

```python
system_prompt = """You are an expert SQL query generator...

CRITICAL RULES:
1. ONLY output the SQL query - no explanations
2. Analyze the database schema carefully
3. Match column names EXACTLY
4. Always end queries with semicolon

INTENT DETECTION - RAW DATA vs AGGREGATION:
When user query contains AGGREGATION keywords use SUM/AVG/COUNT:
  - "total", "sum", "average", "count", "how many"
  - Example: "total south sales" → SELECT SUM(amount)...

When user query asks for RAW DATA use SELECT *:
  - "south sales" without "total" → SELECT * FROM sales WHERE...
  - "show me", "list", "display" → SELECT all matching rows

MULTIPLE VALUES FILTERING:
  - "X and Y sales" → WHERE column IN ('X', 'Y')

INTELLIGENT DATE HANDLING:
  - "January sales" → WHERE EXTRACT(MONTH FROM date) = 1
  - "January 2025" → Filter year AND month
"""
```

#### Why This Prompt Structure?

| Section | Purpose |
|---------|---------|
| **CRITICAL RULES** | Prevents common mistakes (explanations, wrong format) |
| **INTENT DETECTION** | Distinguishes "show data" from "calculate totals" |
| **MULTIPLE VALUES** | Handles "X and Y" patterns with IN clause |
| **DATE HANDLING** | Uses EXTRACT for flexible date filtering |

#### The User Prompt

```python
prompt = f"""DATABASE CONTEXT:
{db_context}

USER QUESTION: {nl_query}

Generate the SQL query that precisely answers this question.
Consider:
1. What data does the user want?
2. Should it be filtered?
3. For DATE queries: Check AVAILABLE YEARS and DATE RANGE
4. Should it be aggregated?
5. Should it be sorted or limited?

SQL QUERY:"""
```

---

### Method: `verify_result()`

Uses LLM to self-verify query correctness.

```python
def verify_result(
    self,
    nl_query: str,
    sql_query: str,
    result_df: pd.DataFrame,
    db_context: str,
    expected_data_info: Dict = None
) -> Dict[str, Any]:
```

#### How Verification Works:

```
┌─────────────────────────────────────────────┐
│ Verification Prompt                         │
├─────────────────────────────────────────────┤
│ USER QUESTION: {nl_query}                   │
│ GENERATED SQL: {sql_query}                  │
│ RESULT DATA: {result_df.to_string()}        │
│                                             │
│ CHECKLIST:                                  │
│ 1. Does SQL interpret question correctly?  │
│ 2. If "all" asked, are ALL rows returned?  │
│ 3. Is filtering correct?                   │
│ 4. Is aggregation correct?                 │
│ 5. Does row count make sense?              │
│                                             │
│ RESPOND:                                    │
│ CORRECT: YES or NO                          │
│ REASON: [explanation]                       │
│ FIX: [if incorrect, what to change]         │
└─────────────────────────────────────────────┘
```

#### Return Value:

```python
{
    "is_correct": True/False,
    "reason": "Query correctly filters by North region",
    "suggested_fix": ""  # Empty if correct
}
```

---

### Method: `_extract_sql()`

Extracts clean SQL from LLM response (which may have markdown, explanations, etc.)

```python
def _extract_sql(self, response: str) -> Optional[str]:
```

#### Extraction Logic:

```
┌────────────────────────────────┐
│ Raw LLM Response               │
│ "Here is the SQL:              │
│ ```sql                         │
│ SELECT * FROM sales;           │
│ ```                            │
│ This query returns all rows."  │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ Step 1: Extract from ```sql``` │
│ SELECT * FROM sales;           │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ Step 2: Remove prefixes        │
│ "SQL:", "Query:", "Answer:"    │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ Step 3: Find SELECT/WITH       │
│ SELECT * FROM sales;           │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ Step 4: Ensure semicolon       │
│ SELECT * FROM sales;           │
└────────────────────────────────┘
```

---

### Method: `_parse_verification()`

Parses LLM verification response into structured format.

```python
def _parse_verification(self, response: str) -> Dict[str, Any]:
    # Look for "CORRECT: NO" or "INCORRECT"
    if "CORRECT: NO" in response.upper():
        result["is_correct"] = False
    
    # Extract REASON: and FIX: sections
    reason_match = re.search(r'REASON:\s*(.+?)(?:FIX:|$)', response)
    fix_match = re.search(r'FIX:\s*(.+?)$', response)
```

---

## Usage in Application

### Called by nl2sql_converter.py:

```python
from src.llm.llm_generator import QwenSQLGenerator

generator = QwenSQLGenerator()

# Generate SQL
sql = generator.generate_sql(
    nl_query="total sales by region",
    db_context=context_string
)

# Verify result
verification = generator.verify_result(
    nl_query="total sales by region",
    sql_query=sql,
    result_df=result_dataframe,
    db_context=context_string
)

if not verification["is_correct"]:
    # Retry with different approach
```

---

## File Relationships

```
llm_generator.py
    │
    ├──> Ollama Server (localhost:11434)
    │        └── qwen2.5-coder:7b-instruct-q4_K_M
    │
    ├──> used by src/llm/nl2sql_converter.py
    │
    └──> imports from src/utils/logger.py
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **First query** | ~5-8 seconds | Model warm-up |
| **Subsequent queries** | ~3-4 seconds | GPU inference |
| **Verification** | ~3-4 seconds | Same as generation |
| **VRAM usage** | ~4.5 GB | 4-bit quantization |
| **Total per query** | ~6-8 seconds | Generate + verify |

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Ollama not running | Returns None, logs error |
| Model not found | Auto-pulls model |
| Generation timeout | 120 second timeout, returns None |
| Invalid SQL in response | Extraction returns None |
| Verification fails | Falls back to "correct" |

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Local Ollama | Privacy, cost, latency |
| qwen2.5-coder | Best code/SQL accuracy |
| 4-bit quantization | Fits consumer GPUs |
| Prompt engineering | Controls output precisely |
| Self-verification | Catches errors before user sees |
| Temperature 0.1 | Consistent, deterministic SQL |
| 120s timeout | Long queries on slow hardware |
