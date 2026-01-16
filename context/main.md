# main.py - Application Entry Point

## File Location
```
nl2sql_assistant/main.py
```

## Purpose
This is the **main entry point** for the NL2SQL Voice Assistant application. It handles:
- Application startup and initialization
- Command-line argument processing
- Database connectivity verification
- GUI application launch
- Error handling and graceful shutdown

---

## Dependencies

```python
import sys                    # Command-line arguments and path manipulation
from pathlib import Path      # Cross-platform path handling

sys.path.append(str(Path(__file__).parent))  # Add project root to Python path

from src.database.db_controller import DatabaseController  # Database operations
from src.gui.main_window import main as gui_main          # GUI launcher
from config import config                                   # Configuration
from src.utils.logger import logger                        # Logging system
```

### Why This Import Structure?

1. **`sys.path.append`**: Ensures Python can find local modules when running from any directory
2. **`Path(__file__).parent`**: Gets the directory containing main.py, regardless of where you run from
3. **Import aliasing**: `main as gui_main` avoids naming conflict with local `main()` function

---

## Code Structure

### Function: `test_database()`

This function performs a comprehensive database connectivity test.

```python
def test_database():
    logger.section("NL2SQL Voice Assistant - Database Test")
    logger.i("TEST", "Starting database connection test")
    db = DatabaseController()

    if db.connect():
        # ... success logic
    else:
        # ... failure logic
```

#### Flow Diagram:

```
┌────────────────────────────────────┐
│ Create DatabaseController instance │
└─────────────────┬──────────────────┘
                  │
                  ▼
         ┌───────────────┐
         │ db.connect()  │
         └───────┬───────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼────┐       ┌────▼────┐
   │ SUCCESS │       │ FAILURE │
   └────┬────┘       └────┬────┘
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────────────┐
│ Get tables    │  │ Print troubleshooting│
│ Check 'sales' │  │ - PostgreSQL running?│
│ Show samples  │  │ - Check credentials  │
│ Show stats    │  │ - DB exists?         │
└───────────────┘  └──────────────────────┘
```

#### What It Tests:
1. **Connection**: Can we connect to PostgreSQL?
2. **Tables**: Does the 'sales' table exist?
3. **Data**: Can we retrieve sample records?
4. **Statistics**: Can we run aggregate queries?

#### Output Examples:

**Success Case:**
```
[DATA] Sample data from sales table:
   id       date    amount    product region  quantity customer_type
0   1 2025-01-15   1549.99     Laptop  North         2      Business

[STATS] Database Statistics:
   total_records  total_sales   avg_sale
0             60     54289.43    904.82
```

**Failure Case - Table Missing:**
```
[WARNING] 'sales' table not found!
   Please run the following steps:
   1. Open pgAdmin
   2. Create database 'nl2sql_db' if it doesn't exist
   3. Run the SQL in 'src/database/schema.sql'
   4. Or run: python src/database/populate_db.py
```

**Failure Case - Connection Failed:**
```
[ERROR] Could not connect to database

[HELP] Troubleshooting:
   1. Make sure PostgreSQL is running
   2. Check credentials in config.py
   3. Verify database 'nl2sql_db' exists

   Current settings:
   - Database: nl2sql_db
   - User: postgres
   - Host: localhost
   - Port: 5432
```

---

### Function: `main()`

The primary entry point that handles application startup.

```python
def main():
    logger.separator("=", 80)
    logger.i("MAIN", "NL2SQL Voice Assistant Starting...")
    logger.separator("=", 80)

    if len(sys.argv) > 1:
        # Handle command-line arguments
    else:
        # Launch GUI
```

#### Command Line Arguments

| Argument | Description |
|----------|-------------|
| (none) | Launch GUI in **local mode** (GPU required) |
| `--test` | Test database connection and exit |
| `--help` | Show help message |
| `--server <url>` | Launch GUI in **remote mode** (connects to server) |

### Examples

```bash
# Local mode (requires GPU, Ollama, PostgreSQL)
python main.py

# Remote mode (lightweight, no GPU needed)
python main.py --server https://abc123.trycloudflare.com

# Test database
python main.py --test

# Show help
python main.py --help
```

---

## Modes of Operation

### Local Mode (Default)

When run without arguments, `main.py` initializes all GPU components locally:
- NL2SQLConverter (Ollama LLM)
- SpeechToText (Whisper Large-v3)
- DatabaseController (PostgreSQL)

### Remote Mode

When run with `--server <url>`, `main.py` uses lightweight HTTP clients:
- RemoteNL2SQLClient → Sends queries to server
- RemoteSpeechToText → Records locally, transcribes on server
- No database connection needed locally

#### How `--test` Works:

```python
if sys.argv[1] == '--test':
    success = test_database()
    if success:
        print("  [OK] All tests passed! Ready to launch GUI")
        print("  Run: python main.py")
    else:
        print("  [WARNING] Please fix database connection first")
    return  # Exit without launching GUI
```

#### Why This Design:
- **Test before run**: Ensures database is properly set up
- **Quick feedback**: Users can diagnose issues without waiting for full GUI load
- **Clear instructions**: Helps new users set up the application

---

### GUI Launch Sequence

When no arguments are provided, the application launches the GUI:

```python
# Verify database connection first
db = DatabaseController()
if not db.connect():
    print("[WARNING] Could not connect to database!")
    print("The application will launch, but queries will fail.")
    input("Press Enter to continue anyway, or Ctrl+C to exit...")
else:
    print("[OK] Database connection OK")
    db.close()

# Launch the GUI
gui_main()
```

#### Flow:

```
┌─────────────────────────────────┐
│ Test database connection        │
└───────────────┬─────────────────┘
                │
       ┌────────┴────────┐
       │                 │
  ┌────▼────┐       ┌────▼────┐
  │ SUCCESS │       │ FAILURE │
  └────┬────┘       └────┬────┘
       │                 │
       │                 ▼
       │          ┌─────────────────┐
       │          │ Show warning    │
       │          │ Wait for user   │
       │          │ Press Enter     │
       │          └────────┬────────┘
       │                   │
       └─────────┬─────────┘
                 │
                 ▼
         ┌───────────────┐
         │ gui_main()    │
         │ Start PyQt6   │
         └───────────────┘
```

#### Why Allow Launch Even With DB Failure?
- GUI still loads for debugging
- User can see the interface
- Configuration can be checked
- Not a hard blocker for development

---

### The `if __name__ == "__main__":` Block

```python
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.i("MAIN", "Application interrupted by user (Ctrl+C)")
        print("\n\nApplication terminated by user")
    except Exception as e:
        logger.e("MAIN", f"Unexpected error in main: {str(e)}", e)
        print(f"\n[ERROR] Unexpected error: {e}")
        print(f"Check log file in logs/ for details")
    finally:
        logger.separator("=", 80)
        logger.i("MAIN", "Application shutdown complete")
        logger.separator("=", 80)
```

#### Exception Handling Strategy:

| Exception Type | Handling |
|----------------|----------|
| **KeyboardInterrupt** | Graceful exit on Ctrl+C, log it, inform user |
| **Exception** | Catch all others, log full details, show user-friendly message |
| **finally** | Always log shutdown, even on errors |

#### Why This Design:
- **KeyboardInterrupt should be clean**: User pressed Ctrl+C intentionally
- **Log everything**: Helps debug issues after the fact
- **finally block**: Ensures shutdown message always logs for log file completeness

---

## Usage Examples

### Running the Application:
```bash
# Launch the GUI (default)
python main.py

# Test database connection
python main.py --test

# Show help
python main.py --help
```

### Typical Startup Output:
```
================================================================================
11:47:59 | INFO     | [MAIN] NL2SQL Voice Assistant Starting...
================================================================================
Launching NL2SQL Voice Assistant GUI...
(Use --test to run database tests, --help for more options)

[OK] Database connection OK
11:47:59 | INFO     | [MAIN] Starting GUI main loop
```

---

## File Relationships

```
main.py
    │
    ├──> imports from config.py (configuration settings)
    │
    ├──> imports from src/database/db_controller.py (database operations)
    │
    ├──> imports from src/gui/main_window.py (GUI application)
    │
    └──> imports from src/utils/logger.py (logging)
```

### Call Hierarchy:

```
main.py::main()
    │
    ├── [--test] ──> test_database()
    │                    └──> DatabaseController
    │                             ├──> connect()
    │                             ├──> get_table_names()
    │                             ├──> execute_query()
    │                             └──> close()
    │
    └── [default] ──> DatabaseController.connect() (verify)
                       │
                       └──> gui_main()
                              └──> MainWindow (PyQt6 GUI loop)
```

---

## Logging

All major events are logged:

| Log Level | Tag | Event |
|-----------|-----|-------|
| INFO | MAIN | Application starting |
| INFO | TEST | Database test starting |
| DEBUG | TEST | Tables found |
| INFO | MAIN | GUI launching |
| WARNING | MAIN | Database connection issues |
| ERROR | MAIN | Unexpected errors |
| INFO | MAIN | Application shutdown |

---

## Design Decisions & Rationale

| Decision | Why |
|----------|-----|
| Test mode available | Verify setup before committing to GUI |
| Warning but continue | Allow partial functionality |
| Extensive logging | Debugging in production |
| finally block | Always log shutdown state |
| Path manipulation | Work from any directory |
| input() for pause | User can read warning before continuing |
