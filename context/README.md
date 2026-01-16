# NL2SQL Voice Assistant - Documentation Index

## Context Directory Structure

This `context/` directory contains **hyper-detailed documentation** for every code file in the NL2SQL Voice Assistant application. Each `.md` file explains:

- What the code does
- Where it is used
- How it works
- Implementation logic
- Design decisions and rationale

---

## Documentation Files

### Core Application

| File | Documented Module | Description |
|------|-------------------|-------------|
| [config.md](config.md) | `config.py` | Application configuration (database, models, UI) |
| [main.md](main.md) | `main.py` | Entry point, startup, CLI arguments |
| [requirements.md](requirements.md) | `requirements.txt` | Python dependencies |

---

### Database Layer (`src/database/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [db_controller.md](db_controller.md) | `db_controller.py` | PostgreSQL operations, queries |
| [schema.md](schema.md) | `schema.sql` | Table structure, indexes, sample data |
| [populate_db.md](populate_db.md) | `populate_db.py` | Database setup script |

---

### LLM Layer (`src/llm/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [llm_generator.md](llm_generator.md) | `llm_generator.py` | Ollama LLM SQL generation |
| [nl2sql_converter.md](nl2sql_converter.md) | `nl2sql_converter.py` | Main conversion pipeline with retry |
| [rag_indexer.md](rag_indexer.md) | `rag_indexer.py` | RAG context retrieval |

---

### GUI Layer (`src/gui/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [main_window.md](main_window.md) | `main_window.py` | PyQt6 GUI, threading, UI components |

---

### Voice Layer (`src/voice/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [speech_to_text.md](speech_to_text.md) | `speech_to_text.py` | Whisper GPU speech recognition |

---

### Reports Layer (`src/reports/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [report_generator.md](report_generator.md) | `report_generator.py` | CSV/Excel/PDF exports |

---

### Utilities (`src/utils/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [logger.md](logger.md) | `logger.py` | Application logging system |

---

### Data Files (`data/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [schema_docs.md](schema_docs.md) | `schema_docs.txt` | RAG knowledge base |

---

### Tests (`tests/`)

| File | Documented Module | Description |
|------|-------------------|-------------|
| [test_comprehensive.md](test_comprehensive.md) | `test_comprehensive.py` | 100 test case suite |

---

## Architecture Overview

```
NL2SQL Voice Assistant
├── main.py                     # Entry point
├── config.py                   # Configuration
│
├── src/
│   ├── database/               # Data layer
│   │   ├── db_controller.py    # PostgreSQL operations
│   │   ├── schema.sql          # Schema definition
│   │   └── populate_db.py      # Data setup
│   │
│   ├── llm/                    # AI layer
│   │   ├── llm_generator.py    # Ollama LLM
│   │   ├── nl2sql_converter.py # Main pipeline
│   │   └── rag_indexer.py      # Context retrieval
│   │
│   ├── gui/                    # Presentation layer
│   │   └── main_window.py      # PyQt6 GUI
│   │
│   ├── voice/                  # Input layer
│   │   └── speech_to_text.py   # Whisper STT
│   │
│   ├── reports/                # Output layer
│   │   └── report_generator.py # Exports
│   │
│   └── utils/                  # Support layer
│       └── logger.py           # Logging
│
├── data/
│   └── schema_docs.txt         # RAG knowledge
│
└── tests/
    └── test_comprehensive.py   # Test suite
```

---

## Data Flow

```
User Voice/Text Input
        │
        ▼
┌───────────────────┐
│ speech_to_text.py │ (if voice)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────┐
│nl2sql_converter.py│◄────│  rag_indexer.py │
└─────────┬─────────┘     └─────────────────┘
          │
          ▼
┌───────────────────┐
│ llm_generator.py  │ ──────► Ollama Server
│ (Qwen2.5-Coder)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ db_controller.py  │ ──────► PostgreSQL
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ main_window.py    │ (display results)
│ report_generator  │ (export)
└───────────────────┘
```

---

## How to Use This Documentation

1. **New to the project?** Start with [main.md](main.md) and [config.md](config.md)
2. **Understanding the LLM?** Read [llm_generator.md](llm_generator.md) and [nl2sql_converter.md](nl2sql_converter.md)
3. **Database questions?** See [db_controller.md](db_controller.md) and [schema.md](schema.md)
4. **GUI modifications?** Check [main_window.md](main_window.md)
5. **Testing?** Review [test_comprehensive.md](test_comprehensive.md)

---

## Technology Stack Summary

| Component | Technology | GPU Accelerated |
|-----------|------------|-----------------|
| GUI | PyQt6 | No |
| Database | PostgreSQL 16 | No |
| LLM | Qwen2.5-Coder via Ollama | **Yes** |
| Speech | Faster-Whisper Large-v3 | **Yes** |
| Charts | Matplotlib | No |
| Exports | pandas, openpyxl, reportlab | No |

---

## Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Application startup | ~10s | Model loading |
| Voice recording | 5s | Configurable |
| Voice transcription | ~3s | GPU (Whisper) |
| SQL generation | ~4s | GPU (Ollama) |
| SQL verification | ~3s | GPU (Ollama) |
| Full query cycle | ~6-10s | Total end-to-end |
| Test suite | ~11min | 100 tests |
