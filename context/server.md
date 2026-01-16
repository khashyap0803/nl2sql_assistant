# server.py - Remote Server Documentation

## File Location
```
nl2sql_assistant/server.py
```

## Purpose
This module exposes the GPU-accelerated NL2SQL services as a REST API server, allowing remote clients to use the application without requiring a powerful GPU.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          HOME PC (Server)                               │
│                          RTX 5060 Ti 16GB GPU                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │   Ollama LLM    │  │  Faster-Whisper │  │     PostgreSQL          │ │
│  │ Qwen2.5-Coder   │  │   Large-v3      │  │     Database            │ │
│  │     (GPU)       │  │     (GPU)       │  │                         │ │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬────────────┘ │
│           │                    │                        │              │
│           └────────────────────┼────────────────────────┘              │
│                                │                                        │
│                    ┌───────────▼───────────┐                           │
│                    │     server.py         │                           │
│                    │   Flask REST API      │                           │
│                    │   localhost:5000      │                           │
│                    └───────────┬───────────┘                           │
│                                │                                        │
│                    ┌───────────▼───────────┐                           │
│                    │  Cloudflare Tunnel    │                           │
│                    │  or Pinggy            │                           │
│                    │  (CGNAT bypass)       │                           │
│                    └───────────┬───────────┘                           │
│                                │                                        │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │
                              HTTPS
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                    REMOTE LAPTOP/PC (Client)                            │
│                    No GPU required                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  python main.py --server https://abc123.trycloudflare.com               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### On Server (Home PC with GPU):

```bash
# 1. Start the server
python server.py

# 2. In another terminal, start Cloudflare Tunnel
cloudflared tunnel --url http://localhost:5000

# 3. Share the generated URL with clients
# Example: https://random-name-1234.trycloudflare.com
```

### On Client (Remote laptop):

```bash
# 1. Install minimal dependencies
pip install -r requirements_client.txt

# 2. Run in remote mode
python main.py --server https://random-name-1234.trycloudflare.com
```

---

## API Endpoints

### GET /api/health
Check server status and service availability.

**Response:**
```json
{
  "status": "online",
  "services": {
    "llm": true,
    "stt": true,
    "database": true
  },
  "gpu": {
    "allocated_gb": 4.5,
    "total_gb": 16.0
  }
}
```

---

### POST /api/query
Convert natural language to SQL and execute.

**Request:**
```json
{
  "query": "show total sales by region"
}
```

**Response:**
```json
{
  "success": true,
  "sql": "SELECT region, SUM(amount) FROM sales GROUP BY region;",
  "result": {
    "columns": ["region", "sum"],
    "data": [["North", 12500.00], ["South", 11200.00]],
    "row_count": 4
  },
  "metadata": {
    "attempts": 1,
    "final_status": "verified_correct"
  }
}
```

---

### POST /api/voice
Transcribe audio to text.

**Request:**
```json
{
  "audio": "<base64 encoded float32 audio>",
  "sample_rate": 16000
}
```

**Response:**
```json
{
  "success": true,
  "text": "show total sales by region"
}
```

---

### POST /api/voice_query
Combined voice transcription + SQL execution.

**Request:**
```json
{
  "audio": "<base64 encoded float32 audio>",
  "sample_rate": 16000
}
```

**Response:**
```json
{
  "success": true,
  "transcribed_text": "show total sales by region",
  "sql": "SELECT region, SUM(amount) FROM sales GROUP BY region;",
  "result": {...}
}
```

---

### GET /api/schema
Get database schema information.

**Response:**
```json
{
  "success": true,
  "tables": ["sales"],
  "schema": {
    "sales": {
      "columns": [
        {"column_name": "id", "data_type": "integer"},
        {"column_name": "amount", "data_type": "numeric"}
      ]
    }
  }
}
```

---

## CGNAT Bypass Methods

### Option 1: Cloudflare Tunnel (Recommended)

**Installation:**
```bash
# Windows
winget install Cloudflare.cloudflared

# Linux/Mac
brew install cloudflared
```

**Usage (Quick Tunnel - no account needed):**
```bash
cloudflared tunnel --url http://localhost:5000
```

Output:
```
Your quick Tunnel has been created! Visit it at:
https://random-name-1234.trycloudflare.com
```

**Permanent Tunnel (requires free Cloudflare account):**
```bash
cloudflared tunnel login
cloudflared tunnel create nl2sql
cloudflared tunnel route dns nl2sql nl2sql.yourdomain.com
cloudflared tunnel run nl2sql
```

---

### Option 2: Pinggy (Simplest)

```bash
ssh -p 443 -R0:localhost:5000 a.pinggy.io
```

Output:
```
https://xxxx.free.pinggy.link
```

---

### Option 3: Ngrok

```bash
ngrok http 5000
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SERVER_HOST | 0.0.0.0 | Host to bind to |
| SERVER_PORT | 5000 | Port to listen on |

---

## Security Considerations

1. **HTTPS**: Cloudflare Tunnel provides automatic HTTPS
2. **Authentication**: Not implemented (add if needed for production)
3. **Rate Limiting**: Not implemented (add flask-limiter if needed)
4. **Private URL**: Quick tunnels generate random URLs

---

## File Relationships

```
server.py
    │
    ├──> Uses: src/llm/nl2sql_converter.py
    ├──> Uses: src/voice/speech_to_text.py
    ├──> Uses: src/database/db_controller.py
    │
    └──> Clients connect via: src/remote/client.py
```
