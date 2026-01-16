# client.py - Remote Client Module

## File Location
```
nl2sql_assistant/src/remote/client.py
```

## Purpose
This module provides lightweight HTTP clients that allow the GUI to run on a client machine while all GPU-intensive processing happens on a remote server. It contains:

1. **RemoteNL2SQLClient** - Mimics NL2SQLConverter interface over HTTP
2. **RemoteSpeechToText** - Mimics SpeechToText interface over HTTP

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLIENT LAPTOP (No GPU)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  main_window.py                                                         │
│       │                                                                 │
│       ├──► RemoteNL2SQLClient                                          │
│       │         │                                                       │
│       │         └──► HTTP POST /api/query ──────────────────────┐      │
│       │                                                          │      │
│       └──► RemoteSpeechToText                                    │      │
│                 │                                                │      │
│                 ├──► sounddevice (local mic)                     │      │
│                 └──► HTTP POST /api/voice ───────────────────────┤      │
│                                                                  │      │
└──────────────────────────────────────────────────────────────────┼──────┘
                                                                   │
                                                              HTTPS│
                                                                   │
┌──────────────────────────────────────────────────────────────────┼──────┐
│                    GPU SERVER (Home PC)                          │      │
├──────────────────────────────────────────────────────────────────┼──────┤
│                                                                  ▼      │
│  server.py (Flask)                                                      │
│       │                                                                 │
│       ├──► NL2SQLConverter (Ollama LLM on GPU)                         │
│       ├──► SpeechToText (Whisper on GPU)                               │
│       └──► DatabaseController (PostgreSQL)                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Class: RemoteNL2SQLClient

HTTP client that provides the same interface as `NL2SQLConverter` but sends requests to a remote server.

### Constructor

```python
def __init__(self, server_url: str):
    self.server_url = server_url.rstrip('/')
    self.enabled = False
    self.timeout = 120  # seconds
    
    if self._check_connection():
        self.enabled = True
```

### Method: `convert_and_execute(nl_query, execute=True)`

Converts natural language to SQL and executes it.

```python
def convert_and_execute(self, nl_query: str, execute: bool = True):
    response = requests.post(
        f"{self.server_url}/api/query",
        json={"query": nl_query},
        timeout=self.timeout
    )
    
    # Parse response
    sql = data.get("sql", "")
    result = pd.DataFrame(data["result"]["data"], 
                          columns=data["result"]["columns"])
    metadata = data.get("metadata", {})
    
    return sql, result, metadata
```

### Method: `get_gpu_memory_usage()`

Gets GPU usage from the server.

```python
def get_gpu_memory_usage(self):
    response = requests.get(f"{self.server_url}/api/health")
    data = response.json()
    return {
        "allocated": data['gpu']['allocated_gb'],
        "total": data['gpu']['total_gb']
    }
```

---

## Class: RemoteSpeechToText

HTTP client that records audio locally and sends it to the server for GPU transcription.

### Constructor

```python
def __init__(self, server_url: str):
    self.server_url = server_url.rstrip('/')
    self.enabled = False
    self.sample_rate = 16000
    self.timeout = 60
    
    if self._check_stt_available():
        self.enabled = True
```

### Method: `listen(duration=5)`

Records audio locally and sends to server for transcription.

```python
def listen(self, duration: int = 5) -> str:
    import sounddevice as sd
    
    # 1. Record audio locally
    audio_data = sd.rec(
        int(duration * self.sample_rate),
        samplerate=self.sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    
    # 2. Convert to base64
    audio_bytes = audio_data.tobytes()
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # 3. Send to server for GPU transcription
    response = requests.post(
        f"{self.server_url}/api/voice",
        json={
            "audio": audio_b64,
            "sample_rate": self.sample_rate
        },
        timeout=self.timeout
    )
    
    return response.json().get("text", "")
```

---

## Usage in GUI

The GUI uses these clients transparently when in remote mode:

```python
# In main_window.py __init__:

if self.remote_mode:
    from src.remote.client import RemoteNL2SQLClient, RemoteSpeechToText
    
    self.converter = RemoteNL2SQLClient(remote_server_url)
    self.stt = RemoteSpeechToText(remote_server_url)
    self.db = None  # No local database needed
else:
    # Local mode - use actual classes
    self.converter = NL2SQLConverter()
    self.stt = SpeechToText()
    self.db = DatabaseController()
```

---

## Dependencies

The remote client only needs lightweight dependencies:

```
PyQt6>=6.5.0       # GUI
requests>=2.28.0   # HTTP client
sounddevice>=0.4.6 # Local audio recording
numpy>=1.24.0      # Audio buffer handling
pandas>=2.0.0      # Result DataFrames
```

**NOT needed on client:**
- faster-whisper (GPU)
- psycopg2 (PostgreSQL)
- ollama (LLM)

---

## Error Handling

```python
try:
    sql, result, metadata = client.convert_and_execute(query)
except requests.exceptions.Timeout:
    return "", None, {"error": "Server timeout"}
except requests.exceptions.ConnectionError:
    return "", None, {"error": "Cannot connect to server"}
except Exception as e:
    return "", None, {"error": str(e)}
```

---

## File Relationships

```
client.py
    │
    ├──> Sends HTTP to: server.py
    │
    ├──> Used by: src/gui/main_window.py (remote mode)
    │
    ├──> Uses: requests (HTTP)
    ├──> Uses: sounddevice (local mic)
    ├──> Uses: numpy (audio buffer)
    └──> Uses: pandas (result DataFrame)
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Base64 for audio | Simple, works over JSON |
| Same interface as local | Drop-in replacement |
| 120s timeout | Long for complex queries |
| Local recording | Reduces latency |
| Server transcription | Uses GPU Whisper |
