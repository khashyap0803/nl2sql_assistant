# NL2SQL Voice Assistant

<div align="center">

**Transform natural language into SQL queries using voice or text input**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://pypi.org/project/PyQt6/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-purple.svg)](https://ollama.ai/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Overview

NL2SQL Voice Assistant is a **GPU-accelerated** desktop application that converts natural language queries (typed or spoken) into SQL, executes them against a PostgreSQL database, and displays the results in a beautiful dark-themed GUI.

### Key Features

| Feature | Description |
|---------|-------------|
| **Voice Input** | Speak your queries using Whisper Large-v3 (GPU) |
| **Text Input** | Type natural language questions |
| **LLM-Powered** | Qwen2.5-Coder 7B via Ollama for SQL generation |
| **RAG System** | Keyword-based schema context retrieval |
| **Self-Verification** | LLM verifies and corrects its own SQL |
| **Export Options** | CSV, Excel, PDF with charts |
| **Remote Mode** | Run GUI on any laptop, processing on GPU server |
| **Dark Theme** | Modern, professional interface |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NL2SQL Voice Assistant                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│   │   Voice     │    │    RAG      │    │   Ollama    │    │ PostgreSQL  │ │
│   │  (Whisper)  │───▶│  Indexer    │───▶│    LLM      │───▶│  Database   │ │
│   │  Large-v3   │    │  (Keyword)  │    │ Qwen2.5-7B  │    │             │ │
│   │    GPU      │    │             │    │    GPU      │    │             │ │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                                      │                  │        │
│         └──────────────────┬───────────────────┴──────────────────┘        │
│                            ▼                                                │
│                    ┌───────────────┐                                       │
│                    │   PyQt6 GUI   │                                       │
│                    │  Dark Theme   │                                       │
│                    └───────────────┘                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | With pip |
| PostgreSQL | 16+ | Running on localhost:5432 |
| Ollama | Latest | GPU-native LLM server |
| NVIDIA GPU | RTX 30/40/50 series | With CUDA drivers |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/khashyap0803/nl2sql_assistant.git
cd nl2sql_assistant

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Ollama and pull the model
# Download from: https://ollama.ai/download
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# 4. Setup the database
# Create database 'nl2sql_db' in PostgreSQL, then:
python src/database/populate_db.py

# 5. Run the application
python main.py
```

---

## Usage

### Local Mode (Default)

Run with full GPU acceleration on your local machine:

```bash
python main.py
```

### Remote Mode (New!)

Access your GPU server from any laptop without installing heavy dependencies:

**On the Server (GPU PC):**
```bash
# Terminal 1: Start the API server
python server.py

# Terminal 2: Start Cloudflare Tunnel (for internet access)
cloudflared tunnel --url http://localhost:5000
# Note the generated URL: https://xxx.trycloudflare.com
```

**On the Client (Laptop):**
```bash
# Install lightweight dependencies only
pip install -r requirements_client.txt

# Connect to the server
python main.py --server https://xxx.trycloudflare.com
```

### Command Line Options

```bash
python main.py                      # Local mode (GPU required)
python main.py --server <url>       # Remote mode (no GPU needed)
python main.py --test               # Test database connection
python main.py --help               # Show help
```

---

## Project Structure

```
nl2sql_assistant/
├── main.py                 # Application entry point
├── server.py               # Remote server API (Flask)
├── config.py               # Configuration settings
├── requirements.txt        # Full dependencies (local mode)
├── requirements_client.txt # Lightweight deps (remote mode)
│
├── src/
│   ├── database/
│   │   ├── db_controller.py    # PostgreSQL operations
│   │   ├── schema.sql          # Database schema
│   │   └── populate_db.py      # Sample data generator
│   │
│   ├── llm/
│   │   ├── llm_generator.py    # Ollama LLM interface
│   │   ├── nl2sql_converter.py # Main conversion pipeline
│   │   └── rag_indexer.py      # RAG context retrieval
│   │
│   ├── gui/
│   │   └── main_window.py      # PyQt6 GUI
│   │
│   ├── voice/
│   │   └── speech_to_text.py   # Whisper STT
│   │
│   ├── remote/
│   │   └── client.py           # Remote server client
│   │
│   ├── reports/
│   │   └── report_generator.py # Export to CSV/Excel/PDF
│   │
│   └── utils/
│       └── logger.py           # Logging system
│
├── data/
│   └── schema_docs.txt         # RAG knowledge base
│
├── context/                    # Detailed documentation
│   ├── README.md               # Documentation index
│   └── *.md                    # Per-file documentation
│
├── tests/
│   ├── test_comprehensive.py   # 100 test cases
│   └── test_integration.py     # Integration tests
│
└── logs/                       # Application logs
```

---

## Configuration

Edit `config.py` to customize:

```python
# Database
database:
  host: localhost
  port: 5432
  dbname: nl2sql_db
  user: postgres
  password: postgres

# LLM
llm:
  model: qwen2.5-coder:7b-instruct-q4_K_M
  temperature: 0.1
  max_tokens: 1024

# Voice
voice:
  model: large-v3
  duration: 5  # seconds

# UI
ui:
  theme: dark
  window_width: 1300
  window_height: 850
```

---

## API Reference (Server Mode)

When running `server.py`, the following REST API endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Server status and GPU info |
| `/api/query` | POST | Convert NL to SQL and execute |
| `/api/voice` | POST | Transcribe audio to text |
| `/api/voice_query` | POST | Voice → SQL → Results |
| `/api/schema` | GET | Database schema info |

### Example: Query Endpoint

```bash
curl -X POST https://your-server/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show total sales by region"}'
```

Response:
```json
{
  "success": true,
  "sql": "SELECT region, SUM(amount) FROM sales GROUP BY region;",
  "result": {
    "columns": ["region", "sum"],
    "data": [["North", 12500.00], ["South", 11200.00]],
    "row_count": 4
  }
}
```

---

## Performance

| Operation | Time | Hardware |
|-----------|------|----------|
| Voice Recording | 5s | Configurable |
| Voice Transcription | ~3s | Whisper Large-v3 on GPU |
| SQL Generation | ~4s | Qwen2.5-Coder 7B on GPU |
| SQL Verification | ~3s | Qwen2.5-Coder 7B on GPU |
| Full Query Cycle | ~6-10s | End-to-end |
| Test Suite (100) | ~11min | All test cases |

### GPU Memory Usage

| Component | VRAM |
|-----------|------|
| Whisper Large-v3 | ~3 GB |
| Qwen2.5-Coder 7B | ~5 GB |
| **Total** | ~8-9 GB |

---

## Testing

Run the comprehensive test suite:

```bash
python tests/test_comprehensive.py
```

This runs 100 test cases across different complexity levels:
- **Simple**: Basic queries (10 tests)
- **Medium**: Aggregations and sorting (20 tests)
- **Complex**: Multi-condition queries (20 tests)
- **Highly Complex**: Window functions, CTEs (50 tests)

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Cannot connect to Ollama" | Run `ollama serve` in a terminal |
| "Database connection failed" | Check PostgreSQL is running and credentials in config.py |
| "DLL initialization failed" | Close other Python processes using GPU |
| "No speech detected" | Check microphone permissions and volume |
| "502 Bad Gateway" (tunnel) | Make sure server.py is running before cloudflared |

### GPU Conflict

If you get a DLL error when running `main.py` while `server.py` is running:

```
Error loading "torch\lib\c10.dll"
```

**Solution**: Use remote mode to connect to your own server:
```bash
python main.py --server http://localhost:5000
```

---

## Documentation

Detailed documentation for every file is available in the `context/` directory:

- [context/README.md](context/README.md) - Documentation index
- [context/config.md](context/config.md) - Configuration system
- [context/main.md](context/main.md) - Entry point
- [context/nl2sql_converter.md](context/nl2sql_converter.md) - Conversion pipeline
- [context/llm_generator.md](context/llm_generator.md) - LLM integration
- [context/server.md](context/server.md) - Remote server API

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| GUI | PyQt6 |
| LLM | Ollama + Qwen2.5-Coder 7B |
| Speech | Faster-Whisper Large-v3 |
| RAG | Keyword-based (custom) |
| Database | PostgreSQL 16 |
| Server | Flask + Flask-CORS |
| Tunnel | Cloudflare Tunnel |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - GPU-accelerated speech recognition
- [Qwen2.5-Coder](https://huggingface.co/Qwen) - Code-specialized LLM
- [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/) - CGNAT bypass

---

<div align="center">

**Built with ❤️ for natural language database querying**

</div>
