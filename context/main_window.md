# main_window.py - GUI Main Window Module

## File Location
```
nl2sql_assistant/src/gui/main_window.py
```

## Purpose
This is the **main graphical user interface (GUI)** for the NL2SQL Voice Assistant. Built with PyQt6, it provides:
- Dark themed, modern interface
- Text and voice input for queries
- Real-time SQL generation and execution
- Results display in table format
- Export to CSV, Excel, PDF
- GPU memory monitoring

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        MainWindow (QMainWindow)                    │
├────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Title Bar: "NL2SQL Voice Assistant v2.0 (GPU Accelerated)"   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ GPU Status: "GPU Memory: 4.5 GB / 16.0 GB"                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Input Section:                                                │ │
│  │ ┌────────────────────────────────────────────────────────┐   │ │
│  │ │ [Text Input Area - Enter your query here...]           │   │ │
│  │ └────────────────────────────────────────────────────────┘   │ │
│  │ [Voice Button]  [Submit Button]  [Clear Button]              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ SQL Output:                                                   │ │
│  │ SELECT region, SUM(amount) FROM sales GROUP BY region...     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Results Table:                                                │ │
│  │ ┌─────────┬─────────────┐                                    │ │
│  │ │ region  │ sum         │                                    │ │
│  │ ├─────────┼─────────────┤                                    │ │
│  │ │ North   │ 12500.00    │                                    │ │
│  │ │ South   │ 11200.00    │                                    │ │
│  │ └─────────┴─────────────┘                                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  [Export CSV]  [Export Excel]  [Export PDF]                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Status Bar: "Ready | LLM: Ollama (GPU) | Whisper: Large-v3"  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## Dependencies

```python
# Internal modules
from src.voice.speech_to_text import SpeechToText      # Voice input
from src.llm.nl2sql_converter import NL2SQLConverter   # SQL generation
from src.database.db_controller import DatabaseController  # DB access
from src.reports.report_generator import ReportGenerator  # Exports
from config import config

# PyQt6 GUI framework
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QStatusBar, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
```

---

## Worker Threads

GUI applications must run long tasks in background threads to stay responsive.

### Class: VoiceWorker

Handles voice recording in a separate thread.

```python
class VoiceWorker(QThread):
    finished = pyqtSignal(str)   # Emits transcribed text
    error = pyqtSignal(str)      # Emits error messages
    status = pyqtSignal(str)     # Emits status updates
    
    def __init__(self, stt, duration=5):
        self.stt = stt           # SpeechToText instance
        self.duration = duration  # Recording seconds
    
    def run(self):
        self.status.emit(f"Recording for {self.duration} seconds...")
        text = self.stt.listen(duration=self.duration)
        if text:
            self.finished.emit(text)
        else:
            self.error.emit("No speech detected")
```

#### Why Threading?
- Recording audio blocks for `duration` seconds
- Without threading, GUI would freeze
- Signals safely communicate back to main thread

### Class: QueryWorker

Handles SQL generation and execution in a separate thread.

```python
class QueryWorker(QThread):
    finished = pyqtSignal(str, object, dict)  # SQL, DataFrame, metadata
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def run(self):
        self.progress.emit("Generating SQL with LLM...")
        sql, result, metadata = self.converter.convert_and_execute(
            self.nl_query, 
            execute=True
        )
        self.finished.emit(sql, result, metadata)
```

#### Why Threading?
- LLM inference takes 5-8 seconds
- GUI would be unresponsive without threading
- Progress updates keep user informed

---

## Class: MainWindow

### Constructor: `__init__()`

```python
def __init__(self):
    super().__init__()
    self.setWindowTitle("NL2SQL Voice Assistant v2.0 (GPU Accelerated)")
    self.setGeometry(100, 100, 1300, 850)
    
    self._apply_dark_theme()
    
    # Initialize components
    self.db = DatabaseController()
    self.db.connect()
    
    self.converter = NL2SQLConverter()   # LLM + RAG
    self.stt = SpeechToText()            # Whisper
    self.report_gen = ReportGenerator()  # Export
    
    self.current_df = None               # Current query results
    self.voice_worker = None
    self.query_worker = None
    
    self.init_ui()
```

#### Initialization Order:
1. Set window properties (title, size)
2. Apply dark theme styling
3. Initialize database connection
4. Initialize NL2SQL converter (LLM)
5. Initialize speech-to-text (Whisper)
6. Initialize report generator
7. Build UI components

---

### Method: `_apply_dark_theme()`

```python
def _apply_dark_theme(self):
    self.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        QLabel {
            color: #e0e0e0;
        }
        QStatusBar {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
    """)
```

#### Color Scheme:
| Element | Color | Hex |
|---------|-------|-----|
| Background | Dark gray | #1e1e1e |
| Text | Light gray | #e0e0e0 |
| Status bar | Slightly lighter | #2d2d2d |
| Accent (title) | Purple gradient | #667eea to #764ba2 |

---

### Method: `init_ui()`

Builds all UI components. Key sections:

1. **Title Label**: Gradient purple header
2. **GPU Status**: Shows VRAM usage
3. **Input Area**: Multi-line text input
4. **Buttons**: Voice, Submit, Clear
5. **SQL Display**: Shows generated SQL
6. **Results Table**: QTableWidget for data
7. **Export Buttons**: CSV, Excel, PDF
8. **Status Bar**: Current state

---

### Method: `process_query()`

Main query processing pipeline.

```python
def process_query(self):
    nl_query = self.input_text.toPlainText().strip()
    
    if not nl_query:
        self.statusBar().showMessage("Please enter a query")
        return
    
    # Disable buttons during processing
    self._set_buttons_enabled(False)
    self.statusBar().showMessage("Processing query...")
    
    # Start worker thread
    self.query_worker = QueryWorker(self.converter, nl_query)
    self.query_worker.finished.connect(self._on_query_complete)
    self.query_worker.error.connect(self._on_query_error)
    self.query_worker.progress.connect(self._on_query_progress)
    self.query_worker.start()
```

---

### Method: `_on_query_complete()`

Handles successful query completion.

```python
def _on_query_complete(self, sql, result, metadata):
    # Display SQL
    self.sql_output.setPlainText(sql)
    
    # Process result
    if isinstance(result, pd.DataFrame):
        self._display_dataframe(result)
        self.current_df = result
        self.statusBar().showMessage(
            f"Query returned {len(result)} rows"
        )
    else:
        self.statusBar().showMessage("No results returned")
    
    self._set_buttons_enabled(True)
```

---

### Method: `_display_dataframe()`

Converts pandas DataFrame to QTableWidget.

```python
def _display_dataframe(self, df):
    self.result_table.setRowCount(len(df))
    self.result_table.setColumnCount(len(df.columns))
    self.result_table.setHorizontalHeaderLabels(df.columns.tolist())
    
    for i, row in df.iterrows():
        for j, col in enumerate(df.columns):
            value = str(row[col])
            item = QTableWidgetItem(value)
            self.result_table.setItem(i, j, item)
```

---

### Method: `start_voice_input()`

Initiates voice recording.

```python
def start_voice_input(self):
    if not self.stt.enabled:
        self._show_message("Warning", "Voice not available")
        return
    
    self.voice_worker = VoiceWorker(self.stt, duration=5)
    self.voice_worker.finished.connect(self._on_voice_complete)
    self.voice_worker.error.connect(self._on_voice_error)
    self.voice_worker.status.connect(self._on_voice_status)
    self.voice_worker.start()
```

---

### Export Methods

#### Export to CSV:
```python
def export_csv(self):
    if self.current_df is None:
        return
    
    filename, _ = QFileDialog.getSaveFileName(
        self, "Export CSV", "", "CSV Files (*.csv)"
    )
    if filename:
        self.report_gen.export_to_csv(self.current_df, filename)
```

#### Export to Excel:
```python
def export_excel(self):
    if self.current_df is None:
        return
    
    filename, _ = QFileDialog.getSaveFileName(
        self, "Export Excel", "", "Excel Files (*.xlsx)"
    )
    if filename:
        self.report_gen.export_to_excel(self.current_df, filename)
```

---

## Function: main()

Application entry point.

```python
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

---

## Signal-Slot Connections

PyQt6 uses signals and slots for event handling:

| Signal | Connected Slot | Purpose |
|--------|---------------|---------|
| submit_btn.clicked | process_query | Run query |
| voice_btn.clicked | start_voice_input | Start recording |
| clear_btn.clicked | clear_all | Clear inputs |
| export_csv_btn.clicked | export_csv | Export results |
| query_worker.finished | _on_query_complete | Handle result |
| voice_worker.finished | _on_voice_complete | Handle transcription |

---

## File Relationships

```
main_window.py
    │
    ├──> imports from src/voice/speech_to_text.py
    │
    ├──> imports from src/llm/nl2sql_converter.py
    │
    ├──> imports from src/database/db_controller.py
    │
    ├──> imports from src/reports/report_generator.py
    │
    ├──> imports from config.py
    │
    └──> called by main.py (gui_main)
```

---

## Threading Model

```
┌─────────────────────────────────────────────┐
│                Main Thread                   │
│           (GUI Event Loop)                   │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼───────┐   ┌───────▼───────┐
│ VoiceWorker   │   │ QueryWorker   │
│ (Recording)   │   │ (LLM + DB)    │
│               │   │               │
│ Signals:      │   │ Signals:      │
│ - finished    │   │ - finished    │
│ - error       │   │ - error       │
│ - status      │   │ - progress    │
└───────────────┘   └───────────────┘
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Dark theme | Modern, easy on eyes |
| Threading | Responsive UI |
| QTableWidget | Native table display |
| Signals/Slots | Thread-safe communication |
| Gradient header | Visual appeal |
| GPU status | User confidence in acceleration |
