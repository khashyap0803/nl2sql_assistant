"""
Main GUI Window for NL2SQL Voice Assistant
Built with PyQt6
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QStatusBar, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.db_controller import DatabaseController
from src.llm.nl2sql_converter import NL2SQLConverter
from src.voice.speech_to_text import SpeechToText
from src.voice.text_to_speech import TextToSpeech
from src.reports.report_generator import ReportGenerator
from config import config


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NL2SQL Voice Assistant v1.0")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize components
        print("Initializing application components...")
        self.db = DatabaseController()
        self.db.connect()
        self.converter = NL2SQLConverter()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.report_gen = ReportGenerator()

        self.current_df = None  # Store current query results

        # Setup UI
        self.init_ui()

        self.statusBar().showMessage("Ready - Connected to database")
        print("✓ Application initialized successfully")

    def init_ui(self):
        """Build the user interface"""
        central = QWidget()
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("🎤 NL2SQL Voice Assistant")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("padding: 15px; background-color: #2196F3; color: white; border-radius: 5px;")
        main_layout.addWidget(title)

        # Input section
        input_group = QWidget()
        input_layout = QVBoxLayout()

        input_label = QLabel("💬 Enter your query:")
        input_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 10px;")
        input_layout.addWidget(input_label)

        # Text input with buttons
        input_row = QHBoxLayout()

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your query here, e.g., 'Show total sales' or 'Sales by region'")
        self.input_text.setMaximumHeight(100)
        self.input_text.setStyleSheet("font-size: 11pt; padding: 5px;")
        input_row.addWidget(self.input_text, stretch=4)

        # Button panel
        button_panel = QVBoxLayout()

        self.mic_btn = QPushButton("🎤 Voice Input")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 10px; 
                font-size: 11pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.mic_btn.clicked.connect(self.handle_voice)
        self.mic_btn.setEnabled(self.stt.enabled)  # Only enable if STT is available

        self.query_btn = QPushButton("▶ Run Query")
        self.query_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                padding: 10px; 
                font-size: 11pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.query_btn.clicked.connect(self.run_query)

        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; 
                color: white; 
                padding: 10px; 
                font-size: 11pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all)

        button_panel.addWidget(self.mic_btn)
        button_panel.addWidget(self.query_btn)
        button_panel.addWidget(self.clear_btn)

        input_row.addLayout(button_panel, stretch=1)
        input_layout.addLayout(input_row)

        # Quick suggestions
        suggestions_label = QLabel("💡 Quick suggestions:")
        suggestions_label.setStyleSheet("font-size: 10pt; margin-top: 5px;")
        input_layout.addWidget(suggestions_label)

        suggestions_row = QHBoxLayout()
        suggestions = self.converter.get_query_suggestions()[:5]
        for suggestion in suggestions:
            btn = QPushButton(suggestion)
            btn.setStyleSheet("padding: 5px; font-size: 9pt;")
            btn.clicked.connect(lambda checked, s=suggestion: self.input_text.setPlainText(s))
            suggestions_row.addWidget(btn)
        suggestions_row.addStretch()
        input_layout.addLayout(suggestions_row)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # SQL Preview section
        sql_label = QLabel("📝 Generated SQL:")
        sql_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
        main_layout.addWidget(sql_label)

        self.sql_text = QTextEdit()
        self.sql_text.setMaximumHeight(80)
        self.sql_text.setReadOnly(True)
        self.sql_text.setStyleSheet("""
            background-color: #f5f5f5; 
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            padding: 5px;
        """)
        main_layout.addWidget(self.sql_text)

        # Results section
        results_label = QLabel("📊 Query Results:")
        results_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
        main_layout.addWidget(results_label)

        self.results_table = QTableWidget()
        self.results_table.setStyleSheet("background-color: white; font-size: 10pt;")
        self.results_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.results_table)

        # Export buttons
        export_row = QHBoxLayout()

        csv_btn = QPushButton("📄 Export CSV")
        csv_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        csv_btn.clicked.connect(lambda: self.export_results('csv'))

        excel_btn = QPushButton("📊 Export Excel")
        excel_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        excel_btn.clicked.connect(lambda: self.export_results('excel'))

        pdf_btn = QPushButton("📋 Export PDF")
        pdf_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        pdf_btn.clicked.connect(lambda: self.export_results('pdf'))

        export_row.addWidget(csv_btn)
        export_row.addWidget(excel_btn)
        export_row.addWidget(pdf_btn)
        export_row.addStretch()

        main_layout.addLayout(export_row)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def handle_voice(self):
        """Handle voice input"""
        self.statusBar().showMessage("🎤 Listening... (speak now)")
        self.mic_btn.setEnabled(False)

        text = self.stt.listen(duration=5)

        self.mic_btn.setEnabled(True)
        if text.strip():
            self.input_text.setPlainText(text)
            self.statusBar().showMessage(f"Heard: {text}")
            self.tts.speak(f"You said: {text}")
        else:
            self.statusBar().showMessage("❌ No speech detected")

    def run_query(self):
        """Execute the natural language query"""
        nl_query = self.input_text.toPlainText().strip()

        if not nl_query:
            QMessageBox.warning(self, "Empty Query", "Please enter a query!")
            return

        self.statusBar().showMessage("🔄 Processing query...")
        self.query_btn.setEnabled(False)

        try:
            # Convert NL to SQL
            sql = self.converter.convert(nl_query)
            self.sql_text.setPlainText(sql)

            # Execute SQL
            result = self.db.execute_query(sql)

            if isinstance(result, str):  # Error
                QMessageBox.critical(self, "Query Error", result)
                self.statusBar().showMessage("❌ Query failed")
            else:  # Success
                self.current_df = result
                self.display_results(result)
                self.statusBar().showMessage(f"✓ Retrieved {len(result)} rows")
                self.tts.speak(f"Query executed successfully. Retrieved {len(result)} rows.")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.statusBar().showMessage("❌ Error occurred")

        self.query_btn.setEnabled(True)

    def display_results(self, df):
        """Display DataFrame in table widget"""
        self.results_table.clear()
        self.results_table.setRowCount(len(df))
        self.results_table.setColumnCount(len(df.columns))
        self.results_table.setHorizontalHeaderLabels(df.columns.tolist())

        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = str(df.iloc[i, j])
                item = QTableWidgetItem(value)
                self.results_table.setItem(i, j, item)

        self.results_table.resizeColumnsToContents()

    def export_results(self, format_type):
        """Export results to file"""
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "No Data", "No results to export!")
            return

        extensions = {
            'csv': ('CSV Files (*.csv)', '.csv'),
            'excel': ('Excel Files (*.xlsx)', '.xlsx'),
            'pdf': ('PDF Files (*.pdf)', '.pdf')
        }

        ext_filter, ext = extensions[format_type]
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            f"nl2sql_report{ext}",
            ext_filter
        )

        if filename:
            try:
                if format_type == 'csv':
                    self.report_gen.export_to_csv(self.current_df, filename)
                elif format_type == 'excel':
                    self.report_gen.export_to_excel(self.current_df, filename)
                elif format_type == 'pdf':
                    self.report_gen.export_to_pdf(self.current_df, filename)

                QMessageBox.information(self, "Success", f"Exported to {filename}")
                self.statusBar().showMessage(f"✓ Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    def clear_all(self):
        """Clear all inputs and results"""
        self.input_text.clear()
        self.sql_text.clear()
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.current_df = None
        self.statusBar().showMessage("Cleared")

    def closeEvent(self, event):
        """Handle window close"""
        self.db.close()
        event.accept()


def main():
    """Launch the application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
