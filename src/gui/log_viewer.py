"""
Log Viewer Window - Real-time log display similar to Android Logcat
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QFont, QColor
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class LogViewerWindow(QMainWindow):
    """Real-time log viewer window similar to Android Logcat"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NL2SQL Assistant - Log Viewer (Logcat)")
        self.setGeometry(200, 200, 1000, 600)

        # Get latest log file
        self.log_file = self.get_latest_log_file()
        self.last_position = 0

        self.init_ui()

        # Setup timer to refresh logs
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_logs)
        self.timer.start(500)  # Refresh every 500ms

    def get_latest_log_file(self):
        """Get the most recent log file"""
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("app_*.log"))
            if log_files:
                return max(log_files, key=lambda p: p.stat().st_mtime)
        return None

    def init_ui(self):
        """Build the user interface"""
        central = QWidget()
        layout = QVBoxLayout()

        # Title bar
        title_layout = QHBoxLayout()
        title_label = QLabel("📋 Application Logs (Logcat View)")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title_layout.addWidget(title_label)

        if self.log_file:
            file_label = QLabel(f"File: {self.log_file.name}")
            file_label.setStyleSheet("font-size: 9pt; color: gray;")
            title_layout.addWidget(file_label)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Filter controls
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Filter:"))

        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.level_filter)

        filter_layout.addWidget(QLabel("Search:"))

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search logs...")
        self.search_box.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_box)

        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(self.clear_btn)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.force_refresh)
        filter_layout.addWidget(self.refresh_btn)

        layout.addLayout(filter_layout)

        # Log display area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier New", 9))
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self.log_display)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        self.line_count_label = QLabel("Lines: 0")
        status_layout.addWidget(self.line_count_label)

        layout.addLayout(status_layout)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # Load initial logs
        self.load_all_logs()

    def load_all_logs(self):
        """Load all logs from the file"""
        if not self.log_file or not self.log_file.exists():
            self.log_display.setPlainText("No log file found. Logs will appear here once the application starts.")
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.log_display.setPlainText(content)
                self.last_position = len(content)

                # Scroll to bottom
                cursor = self.log_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_display.setTextCursor(cursor)

                # Update line count
                line_count = content.count('\n') + 1
                self.line_count_label.setText(f"Lines: {line_count}")
                self.status_label.setText(f"Loaded {len(content)} characters")

        except Exception as e:
            self.log_display.setPlainText(f"Error loading logs: {e}")

    def refresh_logs(self):
        """Refresh logs (only new content)"""
        if not self.log_file or not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()

                if new_content:
                    self.log_display.moveCursor(QTextCursor.MoveOperation.End)
                    self.log_display.insertPlainText(new_content)
                    self.last_position += len(new_content)

                    # Update line count
                    total_content = self.log_display.toPlainText()
                    line_count = total_content.count('\n') + 1
                    self.line_count_label.setText(f"Lines: {line_count}")

                    # Auto-scroll to bottom
                    cursor = self.log_display.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.log_display.setTextCursor(cursor)

        except Exception as e:
            pass  # Silently ignore errors during refresh

    def force_refresh(self):
        """Force full refresh of logs"""
        self.last_position = 0
        self.load_all_logs()
        self.status_label.setText("Refreshed")

    def clear_logs(self):
        """Clear the display (not the file)"""
        self.log_display.clear()
        self.line_count_label.setText("Lines: 0")
        self.status_label.setText("Display cleared")

    def apply_filters(self):
        """Apply level and search filters"""
        # This is a simple filter - in a real implementation,
        # you would re-parse and filter the original content
        self.status_label.setText(f"Filter: {self.level_filter.currentText()}, Search: '{self.search_box.text()}'")

    def closeEvent(self, event):
        """Stop timer when window closes"""
        self.timer.stop()
        event.accept()


def main():
    """Launch log viewer"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = LogViewerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

