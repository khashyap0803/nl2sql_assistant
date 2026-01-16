# logger.py - Application Logging Module

## File Location
```
nl2sql_assistant/src/utils/logger.py
```

## Purpose
This module provides a comprehensive logging system with:
- Console output with colors
- File logging with rotation
- Android-style log levels (v, d, i, w, e, c)
- Specialized logging for queries and database operations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AppLogger                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐│
│  │ Console Handler │    │       File Handler              ││
│  │                 │    │                                 ││
│  │ Format:         │    │ Format:                         ││
│  │ HH:MM:SS | LVL  │    │ DATE TIME | LEVEL | MODULE.FUNC ││
│  │   | message     │    │   | message                     ││
│  │                 │    │                                 ││
│  │ stdout          │    │ logs/app_YYYYMMDD_HHMMSS.log    ││
│  └─────────────────┘    └─────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Class: AppLogger (Singleton)

### Log Levels

```python
VERBOSE = logging.DEBUG - 5   # 5: Extra verbose
DEBUG = logging.DEBUG         # 10: Debug info
INFO = logging.INFO           # 20: Normal info
WARNING = logging.WARNING     # 30: Warnings
ERROR = logging.ERROR         # 40: Errors
CRITICAL = logging.CRITICAL   # 50: Critical errors
```

### Singleton Pattern

```python
_instance = None

def __new__(cls):
    if cls._instance is None:
        cls._instance = super(AppLogger, cls).__new__(cls)
        cls._instance._initialize()
    return cls._instance
```

**Why Singleton?**
- Single logging configuration
- Consistent log file across modules
- Shared state for handlers

---

### Method: `_initialize()`

Sets up logging handlers.

```python
def _initialize(self):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    self._logger = logging.getLogger("NL2SQL_App")
    self._logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    self._logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    self._logger.addHandler(console_handler)
    self._logger.addHandler(file_handler)
    
    self.log_file = log_file
```

#### Log File Naming:
```
logs/app_20260116_114754.log
      ^^^  ^^^^   ^^^^^^
      year month  time
           day
```

---

### Android-Style Methods

Short method names inspired by Android's Log class:

| Method | Level | Example |
|--------|-------|---------|
| `v(tag, msg)` | VERBOSE | Extra debug details |
| `d(tag, msg)` | DEBUG | Debug information |
| `i(tag, msg)` | INFO | Normal events |
| `w(tag, msg)` | WARNING | Potential issues |
| `e(tag, msg)` | ERROR | Errors |
| `c(tag, msg)` | CRITICAL | Fatal errors |

```python
def v(self, tag: str, message: str):
    self._logger.log(self.VERBOSE, f"[{tag}] {message}")

def d(self, tag: str, message: str):
    self._logger.debug(f"[{tag}] {message}")

def i(self, tag: str, message: str):
    self._logger.info(f"[{tag}] {message}")

def w(self, tag: str, message: str):
    self._logger.warning(f"[{tag}] {message}")

def e(self, tag: str, message: str, exc_info: Optional[Exception] = None):
    if exc_info:
        self._logger.error(f"[{tag}] {message}", exc_info=True)
    else:
        self._logger.error(f"[{tag}] {message}")

def c(self, tag: str, message: str):
    self._logger.critical(f"[{tag}] {message}")
```

---

### Specialized Methods

#### Query Logging:
```python
def query_log(self, nl_query: str, sql_query: str, success: bool = True):
    status = "[OK]" if success else "[FAIL]"
    self.i("QUERY", f"{status} NL: '{nl_query}'")
    self.d("QUERY", f"   SQL: {sql_query}")
```

#### Database Logging:
```python
def db_log(self, operation: str, details: str, success: bool = True):
    status = "[OK]" if success else "[FAIL]"
    self.i("DATABASE", f"{status} {operation}: {details}")
```

#### GUI Logging:
```python
def gui_log(self, component: str, action: str):
    self.d("GUI", f"{component} - {action}")
```

---

### Utility Methods

```python
def separator(self, char: str = "=", length: int = 80):
    self._logger.info(char * length)

def section(self, title: str):
    self.separator()
    self._logger.info(f"  {title}")
    self.separator()
```

---

## Module-Level Convenience Functions

```python
logger = AppLogger()

def log_debug(tag: str, message: str):
    logger.d(tag, message)

def log_info(tag: str, message: str):
    logger.i(tag, message)

def log_warning(tag: str, message: str):
    logger.w(tag, message)

def log_error(tag: str, message: str, exc: Optional[Exception] = None):
    logger.e(tag, message, exc)

def log_query(nl_query: str, sql_query: str, success: bool = True):
    logger.query_log(nl_query, sql_query, success)

def log_db(operation: str, details: str, success: bool = True):
    logger.db_log(operation, details, success)
```

---

## Output Examples

### Console Output:
```
11:47:54 | INFO     | ================================================================================
11:47:54 | INFO     | Application Logger Initialized
11:47:54 | INFO     | Log file: logs/app_20260116_114754.log
11:47:54 | INFO     | ================================================================================
11:47:55 | INFO     | [NL2SQL_INIT] Initializing NL2SQL Converter (RAG + Ollama LLM)
11:47:57 | INFO     | [OLLAMA] Connected to Ollama server
11:47:59 | DEBUG    | [LLM_INIT] Available models: ['qwen2.5-coder:7b-instruct-q4_K_M']
11:47:59 | INFO     | [DATABASE] [OK] Connection: Successfully connected to nl2sql_db
```

### File Output:
```
2026-01-16 11:47:54 | INFO     | NL2SQL_App | logger._initialize:56 | Application Logger Initialized
2026-01-16 11:47:55 | INFO     | NL2SQL_App | nl2sql_converter.__init__:25 | [NL2SQL_INIT] Initializing NL2SQL Converter
2026-01-16 11:47:57 | INFO     | NL2SQL_App | llm_generator._check_connection:28 | [OLLAMA] Connected to Ollama server
```

---

## Usage in Application

```python
from src.utils.logger import logger, log_db, log_error

# Using logger instance directly
logger.i("MAIN", "Application starting...")
logger.d("DB", f"Connection params: {params}")
logger.w("LLM", "Response was truncated")
logger.e("ERROR", "Query failed", exception)

# Using convenience functions
log_db("Connection", "Connected to nl2sql_db", success=True)
log_error("QUERY", f"SQL error: {error}", exception)

# Sections for visual separation
logger.section("Database Test Results")
```

---

## File Relationships

```
logger.py
    │
    ├──> Creates: logs/app_YYYYMMDD_HHMMSS.log
    │
    ├──> used by: All modules in the application
    │       ├── main.py
    │       ├── db_controller.py
    │       ├── nl2sql_converter.py
    │       ├── llm_generator.py
    │       ├── rag_indexer.py
    │       ├── main_window.py
    │       └── speech_to_text.py
    │
    └──> Standard library: logging
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Singleton | Consistent logging across app |
| Tag-based | Easy filtering and searching |
| Dual output | Console for dev, file for debug |
| Timestamped files | No overwriting, easy debugging |
| Android-style | Short, familiar API |
| UTF-8 encoding | Support special characters |
