# config.py - Application Configuration Module

## File Location
```
nl2sql_assistant/config.py
```

## Purpose
This module provides a centralized configuration management system for the entire NL2SQL Voice Assistant application. It handles loading, saving, and accessing configuration values from a JSON file with fallback defaults.

---

## Dependencies

```python
import json          # For reading/writing JSON configuration files
from pathlib import Path  # For cross-platform file path handling
```

### Why These Dependencies?
- **json**: Native Python library for JSON serialization. Chosen because:
  - Configuration files are human-readable
  - No external dependencies required
  - Easy to edit manually if needed
- **pathlib.Path**: Modern Pythonic file handling that works on Windows/Linux/Mac

---

## Code Structure

### Class: Config

The `Config` class implements the **Singleton Pattern** implicitly - a single instance (`config`) is created at module load time and shared across the application.

---

### DEFAULT_CONFIG Dictionary

```python
DEFAULT_CONFIG = {
    'database': {
        'dbname': 'nl2sql_db',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',
        'port': 5432
    },
    'models': {
        'llm': 'qwen2.5-coder:7b-instruct-q4_K_M',
        'whisper': 'large-v3'
    },
    'voice': {
        'recording_duration': 5
    },
    'ui': {
        'theme': 'dark',
        'window_width': 1300,
        'window_height': 850
    }
}
```

#### Configuration Sections Explained:

| Section | Key | Value | Description |
|---------|-----|-------|-------------|
| **database** | dbname | nl2sql_db | PostgreSQL database name |
| | user | postgres | Database username |
| | password | postgres | Database password |
| | host | localhost | Database server address |
| | port | 5432 | PostgreSQL default port |
| **models** | llm | qwen2.5-coder:7b-instruct-q4_K_M | Ollama LLM model for SQL generation |
| | whisper | large-v3 | Faster-Whisper model for speech recognition |
| **voice** | recording_duration | 5 | Seconds to record audio |
| **ui** | theme | dark | Application color theme |
| | window_width | 1300 | Initial window width in pixels |
| | window_height | 850 | Initial window height in pixels |

#### Why These Defaults?
- **qwen2.5-coder:7b-instruct-q4_K_M**: Best balance of speed and accuracy for SQL generation on consumer GPUs, 4-bit quantization for memory efficiency
- **whisper large-v3**: Most accurate speech recognition model from OpenAI, runs on GPU via CTranslate2
- **5 seconds recording**: Good balance for natural language queries without being too long

---

### Method: `__init__(self, config_file='config.json')`

```python
def __init__(self, config_file='config.json'):
    self.config_file = Path(config_file)
    self.config = self.load_config()
```

#### What It Does:
1. Accepts an optional configuration file path (defaults to `config.json` in the project root)
2. Converts the path to a `Path` object for cross-platform compatibility
3. Immediately loads the configuration

#### Why This Design:
- Default filename allows the app to work immediately without any setup
- Path object enables checking if file exists without OS-specific code

---

### Method: `load_config(self)`

```python
def load_config(self):
    if self.config_file.exists():
        try:
            with open(self.config_file, 'r') as f:
                loaded = json.load(f)
                return {**self.DEFAULT_CONFIG, **loaded}
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return self.DEFAULT_CONFIG.copy()
    return self.DEFAULT_CONFIG.copy()
```

#### Logic Flow:
```
┌─────────────────────────────┐
│ Does config.json exist?     │
└────────────┬────────────────┘
             │
        ┌────┴────┐
        │ Yes     │ No ────────────> Return DEFAULT_CONFIG
        └────┬────┘
             │
             ▼
┌─────────────────────────────┐
│ Try to parse JSON file      │
└────────────┬────────────────┘
             │
        ┌────┴────┐
        │Success  │ Error ─────────> Print warning, return DEFAULT_CONFIG
        └────┬────┘
             │
             ▼
┌─────────────────────────────┐
│ Merge with defaults         │
│ {**DEFAULT, **loaded}       │
│ User values override        │
└─────────────────────────────┘
```

#### Why This Logic:
- **Graceful degradation**: App works even without config.json
- **Merge with defaults**: New config options added to defaults won't break existing installations
- **Error handling**: Corrupted config files don't crash the app
- **`{**dict1, **dict2}`**: Python dictionary unpacking, second dict values override first

---

### Method: `save_config(self)`

```python
def save_config(self):
    try:
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration saved to {self.config_file}")
    except Exception as e:
        print(f"Error saving config: {e}")
```

#### What It Does:
1. Serializes current configuration to JSON
2. Writes to the config file with pretty formatting (indent=2)
3. Prints confirmation or error message

#### Why `indent=2`:
- Makes the JSON human-readable
- Easy to edit manually if needed
- Standard formatting for config files

---

### Method: `get(self, *keys)`

```python
def get(self, *keys):
    value = self.config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, {})
        else:
            return None
    return value
```

#### How It Works:
Uses **variadic arguments** (`*keys`) to access nested configuration values.

#### Usage Examples:
```python
# Single level access
config.get('database')  
# Returns: {'dbname': 'nl2sql_db', 'user': 'postgres', ...}

# Nested access
config.get('database', 'dbname')  
# Returns: 'nl2sql_db'

# Deep nested access
config.get('models', 'llm')  
# Returns: 'qwen2.5-coder:7b-instruct-q4_K_M'

# Non-existent key
config.get('nonexistent', 'key')  
# Returns: {} (empty dict, not None!)
```

#### Why This Design:
- **Variadic arguments**: Cleaner than `config['database']['dbname']`
- **Safe navigation**: Returns `{}` for missing keys instead of raising KeyError
- **Flexible depth**: Works for any nesting level

---

### Method: `set(self, value, *keys)`

```python
def set(self, value, *keys):
    if len(keys) == 1:
        self.config[keys[0]] = value
    else:
        current = self.config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value
    self.save_config()
```

#### How It Works:
1. If single key, directly sets the value
2. If multiple keys, navigates/creates nested structure
3. **Always saves** after setting (auto-persist)

#### Usage Examples:
```python
# Set simple value
config.set('newdb', 'database', 'dbname')

# Set new nested value (creates path if needed)
config.set('value', 'new', 'nested', 'path')
# Creates: {'new': {'nested': {'path': 'value'}}}
```

#### Why `setdefault`:
- Creates missing intermediate dictionaries automatically
- No need to check if keys exist before setting nested values

---

## Module-Level Exports

```python
config = Config()
DB_CONFIG = config.get('database')
```

### What Gets Exported:
1. **`config`**: The global Config instance, usable as `from config import config`
2. **`DB_CONFIG`**: Shortcut to database settings, used by db_controller.py

### Why Module-Level Initialization:
- Config is loaded once at import time
- All modules share the same configuration instance
- No need to pass config around as parameter

---

## Usage in Other Modules

### In db_controller.py:
```python
from config import DB_CONFIG

class DatabaseController:
    def __init__(self):
        self.conn_params = {
            'dbname': DB_CONFIG.get('dbname'),
            'user': DB_CONFIG.get('user'),
            ...
        }
```

### In main.py:
```python
from config import config

print(f"Database: {config.get('database', 'dbname')}")
```

### In main_window.py:
```python
from config import config

width = config.get('ui', 'window_width')
height = config.get('ui', 'window_height')
```

---

## File Relationships

```
config.py
    │
    ├──> config.json (optional, created on save)
    │
    ├──> main.py (reads database and model settings)
    │
    ├──> src/database/db_controller.py (reads database connection)
    │
    ├──> src/gui/main_window.py (reads UI settings)
    │
    └──> src/llm/llm_generator.py (model name from config)
```

---

## Configuration File Example

When saved, `config.json` looks like:

```json
{
  "database": {
    "dbname": "nl2sql_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
  },
  "models": {
    "llm": "qwen2.5-coder:7b-instruct-q4_K_M",
    "whisper": "large-v3"
  },
  "voice": {
    "recording_duration": 5
  },
  "ui": {
    "theme": "dark",
    "window_width": 1300,
    "window_height": 850
  }
}
```

---

## Design Decisions & Rationale

| Decision | Why |
|----------|-----|
| JSON format | Human-readable, no dependencies, easy to edit |
| Singleton pattern | All modules share same config state |
| Default fallback | App works without config.json |
| Auto-save on set | Prevents forgetting to save changes |
| Variadic get/set | Clean API for nested access |
| Path object | Cross-platform file handling |
