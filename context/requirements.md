# requirements.txt - Python Dependencies

## File Location
```
nl2sql_assistant/requirements.txt
```

## Purpose
This file lists all Python package dependencies required to run the NL2SQL Voice Assistant. It's used by `pip` to install all necessary libraries in one command.

---

## Installation Command

```bash
pip install -r requirements.txt
```

---

## Dependencies Breakdown

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| **PyQt6** | >=6.5.0 | GUI framework for the desktop application |
| **psycopg2-binary** | >=2.9.0 | PostgreSQL database adapter for Python |
| **pandas** | >=2.0.0 | Data manipulation and analysis (query results) |
| **numpy** | >=1.24.0 | Numerical operations (required by pandas/matplotlib) |

#### PyQt6 Explained:
- Modern Python binding for Qt6 framework
- Cross-platform (Windows, Linux, Mac)
- Native-looking GUI widgets
- Replaces older PyQt5/PySide2

#### psycopg2-binary Explained:
- `-binary` suffix means pre-compiled (no C compiler needed)
- Most popular PostgreSQL adapter for Python
- Supports connection pooling, async queries, prepared statements

---

### Speech-to-Text (GPU Accelerated)

| Package | Version | Purpose |
|---------|---------|---------|
| **faster-whisper** | >=1.0.0 | OpenAI Whisper reimplemented with CTranslate2 |
| **sounddevice** | >=0.4.6 | Audio recording from microphone |
| **scipy** | >=1.10.0 | Scientific computing (audio processing) |

#### faster-whisper Explained:
- **4x faster** than original OpenAI Whisper
- Uses **CTranslate2** backend (not PyTorch)
- Supports **GPU acceleration** via CUDA
- Models: tiny, base, small, medium, large-v2, large-v3
- We use **large-v3** for best accuracy

#### Why faster-whisper over original Whisper?
| Feature | Original Whisper | Faster-Whisper |
|---------|-----------------|----------------|
| Backend | PyTorch | CTranslate2 |
| Speed | 1x | 4x |
| Memory | High | 50-70% less |
| GPU Support | CUDA | CUDA + TensorRT |
| Quantization | No | INT8, FP16 |

---

### LLM Communication

| Package | Version | Purpose |
|---------|---------|---------|
| **requests** | >=2.28.0 | HTTP client for Ollama API |

#### Why requests?
- Ollama runs as a local HTTP server
- We send prompts via REST API
- No heavy ML libraries needed (Ollama handles the LLM)
- Simple, reliable, well-documented

---

### Visualization

| Package | Version | Purpose |
|---------|---------|---------|
| **matplotlib** | >=3.7.0 | Chart generation (bar, line, pie) |
| **plotly** | >=5.14.0 | Interactive charts (optional, for future use) |

#### matplotlib Explained:
- Static chart generation
- Used in `report_generator.py`
- Creates PNG/PDF charts from query results
- Non-interactive backend (`Agg`) for server-side rendering

---

### Export Formats

| Package | Version | Purpose |
|---------|---------|---------|
| **reportlab** | >=4.0.0 | PDF generation |
| **openpyxl** | >=3.1.0 | Excel file (.xlsx) export |

#### reportlab Explained:
- Pure Python PDF generator
- Creates tables, charts in PDF format
- Used for report exports

#### openpyxl Explained:
- Read/write Excel 2010+ files
- Used for `.xlsx` exports
- Supports formatting, formulas (though we use simple data export)

---

### Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| **tqdm** | >=4.65.0 | Progress bars (model loading, etc.) |
| **pyyaml** | >=6.0.0 | YAML parsing (optional config formats) |

---

## External Requirements (Not in pip)

These must be installed separately as they are system-level applications:

### 1. Ollama - LLM Server (GPU Native)

```bash
# Download from: https://ollama.ai/download
# Then pull the model:
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

#### What is Ollama?
- Local LLM inference server
- Runs models on your GPU (no cloud needed)
- Simple HTTP API at `localhost:11434`
- Manages model downloads and quantization

#### Why qwen2.5-coder:7b-instruct-q4_K_M?
| Choice | Reason |
|--------|--------|
| qwen2.5-coder | Specialized for code generation (including SQL) |
| 7b | 7 billion parameters - good balance of speed/accuracy |
| instruct | Fine-tuned to follow instructions |
| q4_K_M | 4-bit quantization, ~4GB VRAM, fast inference |

---

### 2. PostgreSQL - Database

```bash
# Download from: https://www.postgresql.org/download/
```

#### Why PostgreSQL?
- Open source, free, enterprise-ready
- Excellent SQL standard compliance
- Rich data types (JSON, arrays, etc.)
- Used by many production systems

---

### 3. NVIDIA GPU Drivers + CUDA

For GPU acceleration (required for speech recognition):

```
RTX 5060 Ti (Blackwell): Game Ready Driver 575+
CUDA Toolkit: 12.x
```

---

## Dependency Tree

```
requirements.txt
│
├── PyQt6 ──────────────────> GUI windows, widgets, dialogs
│
├── psycopg2-binary ────────> PostgreSQL connection
│       └── libpq (system)
│
├── pandas ─────────────────> DataFrames for query results
│       └── numpy
│
├── faster-whisper ─────────> Speech recognition
│       ├── ctranslate2
│       ├── tokenizers
│       └── huggingface-hub
│
├── sounddevice ────────────> Microphone recording
│       └── PortAudio (system)
│
├── matplotlib ─────────────> Chart generation
│       └── numpy
│
├── reportlab ──────────────> PDF export
│
└── openpyxl ───────────────> Excel export
```

---

## Version Pinning Strategy

We use **minimum version constraints** (`>=`) rather than exact versions (`==`):

| Strategy | Example | Reason |
|----------|---------|--------|
| Minimum | `>=6.5.0` | Allows security updates |
| Exact | `==6.5.0` | Could block security fixes |
| Range | `>=6.5.0,<7.0.0` | Allows patches, blocks major changes |

**Our choice**: Minimum versions for flexibility, assuming users want latest stable.

---

## Creating a Virtual Environment

Recommended setup:

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Updating Dependencies

To update all packages to latest compatible versions:

```bash
pip install --upgrade -r requirements.txt
```

To freeze current versions (for reproducibility):

```bash
pip freeze > requirements-lock.txt
```

---

## Troubleshooting

### Issue: psycopg2 installation fails
```bash
# Solution: Use binary version (already in requirements)
pip install psycopg2-binary
```

### Issue: PyQt6 import error
```bash
# Solution: Install system dependencies (Linux)
sudo apt-get install python3-pyqt6
```

### Issue: sounddevice fails
```bash
# Solution: Install PortAudio (Linux)
sudo apt-get install portaudio19-dev
```

### Issue: faster-whisper CUDA error
```
# Solution: Ensure CUDA toolkit matches GPU driver
# RTX 5060 Ti needs CUDA 12.x, driver 575+
```
