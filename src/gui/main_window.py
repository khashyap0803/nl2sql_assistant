import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.reports.report_generator import ReportGenerator
from config import config

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QStatusBar, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


class VoiceWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def __init__(self, stt, duration=5):
        super().__init__()
        self.stt = stt
        self.duration = duration
    
    def run(self):
        try:
            self.status.emit(f"Recording for {self.duration} seconds...")
            text = self.stt.listen(duration=self.duration)
            if text:
                self.status.emit("Voice recorded, processing...")
                self.finished.emit(text)
            else:
                self.error.emit("No speech detected")
        except Exception as e:
            self.error.emit(str(e))


class QueryWorker(QThread):
    finished = pyqtSignal(str, object, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, converter, nl_query):
        super().__init__()
        self.converter = converter
        self.nl_query = nl_query
    
    def run(self):
        try:
            self.progress.emit("Generating SQL with LLM...")
            sql, result, metadata = self.converter.convert_and_execute(
                self.nl_query, 
                execute=True
            )
            self.finished.emit(sql, result, metadata)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self, remote_server_url=None):
        super().__init__()
        self.remote_mode = remote_server_url is not None
        
        if self.remote_mode:
            self.setWindowTitle("NL2SQL Voice Assistant v2.0 (Remote Mode)")
        else:
            self.setWindowTitle("NL2SQL Voice Assistant v2.0 (GPU Accelerated)")
        self.setGeometry(100, 100, 1300, 850)
        
        self._apply_dark_theme()
        
        print("Initializing application components...")
        
        if self.remote_mode:
            print(f"Remote mode: {remote_server_url}")
            from src.remote.client import RemoteNL2SQLClient, RemoteSpeechToText
            
            print("Connecting to remote NL2SQL service...")
            self.converter = RemoteNL2SQLClient(remote_server_url)
            
            print("Connecting to remote STT service...")
            self.stt = RemoteSpeechToText(remote_server_url)
            
            self.db = None
        else:
            from src.database.db_controller import DatabaseController
            from src.llm.nl2sql_converter import NL2SQLConverter
            from src.voice.speech_to_text import SpeechToText
            
            self.db = DatabaseController()
            self.db.connect()
            
            print("Loading NL2SQL Converter (RAG + LLM)...")
            self.converter = NL2SQLConverter()
            
            print("Loading Whisper Large-v3 on GPU...")
            self.stt = SpeechToText()
        
        self.report_gen = ReportGenerator()
        
        self.current_df = None
        self.voice_worker = None
        self.query_worker = None
        
        self.init_ui()
        
        if self.remote_mode:
            status_msg = "Ready | Remote Mode"
            if self.converter.enabled:
                status_msg += " | Server Connected"
        else:
            status_msg = "Ready"
            if self.converter.enabled:
                status_msg += " | LLM: Ollama (GPU)"
            if self.stt.enabled:
                status_msg += " | Whisper: Large-v3 (GPU)"
        
        self.statusBar().showMessage(status_msg)
        print("Application initialized successfully")

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

    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("NL2SQL Voice Assistant")
        title_font = QFont("Segoe UI", 20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            padding: 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            color: white;
            border-radius: 8px;
        """)
        main_layout.addWidget(title)

        gpu_status = QLabel()
        if self.converter.enabled:
            mem = self.converter.get_gpu_memory_usage()
            if mem:
                gpu_status.setText(f"GPU Memory: {mem.get('allocated', 0):.1f} GB / {mem.get('total', 0):.1f} GB")
            else:
                gpu_status.setText("GPU: Active")
        else:
            gpu_status.setText("GPU: Not Available")
        gpu_status.setStyleSheet("color: #888; font-size: 10pt; padding: 5px;")
        gpu_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(gpu_status)

        input_label = QLabel("Enter your query (text or voice):")
        input_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 10px; color: #e0e0e0;")
        main_layout.addWidget(input_label)

        input_row = QHBoxLayout()

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Type your query here...\n\n"
            "Examples:\n"
            "- Show total sales by product\n"
            "- Top 5 products by revenue in the North region\n"
            "- Average sales amount for business customers"
        )
        self.input_text.setMaximumHeight(120)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                font-size: 11pt;
                padding: 10px;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QTextEdit:focus {
                border: 1px solid #667eea;
            }
        """)
        input_row.addWidget(self.input_text, stretch=4)

        button_panel = QVBoxLayout()
        button_panel.setSpacing(8)

        self.mic_btn = QPushButton("Voice Input")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.mic_btn.clicked.connect(self.handle_voice)
        self.mic_btn.setEnabled(self.stt.enabled)

        self.query_btn = QPushButton("Run Query")
        self.query_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                padding: 12px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6fd6;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            QPushButton:pressed {
                background-color: #4e5fc2;
            }
        """)
        self.query_btn.clicked.connect(self.run_query)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 12px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all)

        button_panel.addWidget(self.mic_btn)
        button_panel.addWidget(self.query_btn)
        button_panel.addWidget(self.clear_btn)

        input_row.addLayout(button_panel, stretch=1)
        main_layout.addLayout(input_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: #667eea;
            }
        """)
        self.progress_bar.setMaximum(0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        sql_label = QLabel("Generated SQL:")
        sql_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px; color: #e0e0e0;")
        main_layout.addWidget(sql_label)

        self.sql_text = QTextEdit()
        self.sql_text.setMaximumHeight(100)
        self.sql_text.setReadOnly(True)
        self.sql_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #00ff88;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11pt;
                padding: 10px;
                border: 1px solid #444;
                border-radius: 6px;
            }
        """)
        main_layout.addWidget(self.sql_text)

        self.verification_label = QLabel("")
        self.verification_label.setStyleSheet("font-size: 10pt; color: #888; padding: 5px;")
        main_layout.addWidget(self.verification_label)

        results_label = QLabel("Query Results:")
        results_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px; color: #e0e0e0;")
        main_layout.addWidget(results_label)

        self.results_table = QTableWidget()
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 6px;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #667eea;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            QHeaderView::section {
                background-color: #383838;
                color: #e0e0e0;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #667eea;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #383838;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
        """)
        self.results_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.results_table)

        export_row = QHBoxLayout()

        export_style = """
            QPushButton {
                background-color: #383838;
                color: #e0e0e0;
                padding: 10px 20px;
                font-size: 10pt;
                border-radius: 5px;
                border: 1px solid #555;
            }
            QPushButton:hover {
                background-color: #444;
                border-color: #667eea;
            }
        """

        csv_btn = QPushButton("Export CSV")
        csv_btn.setStyleSheet(export_style)
        csv_btn.clicked.connect(lambda: self.export_results('csv'))

        excel_btn = QPushButton("Export Excel")
        excel_btn.setStyleSheet(export_style)
        excel_btn.clicked.connect(lambda: self.export_results('excel'))

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.setStyleSheet(export_style)
        pdf_btn.clicked.connect(lambda: self.export_results('pdf'))

        export_row.addWidget(csv_btn)
        export_row.addWidget(excel_btn)
        export_row.addWidget(pdf_btn)
        export_row.addStretch()

        main_layout.addLayout(export_row)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def handle_voice(self):
        if not self.stt.enabled:
            QMessageBox.warning(self, "Voice Not Available", "Whisper is not initialized")
            return
        
        self.statusBar().showMessage("Recording for 5 seconds... speak now!")
        self.mic_btn.setEnabled(False)
        self.mic_btn.setText("Recording...")
        self.progress_bar.show()
        
        self.voice_worker = VoiceWorker(self.stt, duration=5)
        self.voice_worker.finished.connect(self.on_voice_finished)
        self.voice_worker.error.connect(self.on_voice_error)
        self.voice_worker.status.connect(lambda s: self.statusBar().showMessage(s))
        self.voice_worker.start()

    def on_voice_finished(self, text):
        self.progress_bar.hide()
        self.mic_btn.setEnabled(True)
        self.mic_btn.setText("Voice Input")
        
        if text.strip():
            self.input_text.setPlainText(text)
            self.statusBar().showMessage(f"Transcribed: {text[:50]}... Running query...")
            self.run_query()
        else:
            self.statusBar().showMessage("No speech detected")

    def on_voice_error(self, error):
        self.progress_bar.hide()
        self.mic_btn.setEnabled(True)
        self.mic_btn.setText("Voice Input")
        self.statusBar().showMessage(f"Voice error: {error}")
        QMessageBox.warning(self, "Voice Error", str(error))

    def run_query(self):
        nl_query = self.input_text.toPlainText().strip()

        if not nl_query:
            QMessageBox.warning(self, "Empty Query", "Please enter a query!")
            return

        self.statusBar().showMessage("Processing query with LLM...")
        self.query_btn.setEnabled(False)
        self.progress_bar.show()
        self.verification_label.setText("Generating SQL...")
        
        self.query_worker = QueryWorker(self.converter, nl_query)
        self.query_worker.finished.connect(self.on_query_finished)
        self.query_worker.error.connect(self.on_query_error)
        self.query_worker.progress.connect(self.on_query_progress)
        self.query_worker.start()

    def on_query_progress(self, status):
        self.verification_label.setText(status)

    def on_query_finished(self, sql, result, metadata):
        self.progress_bar.hide()
        self.query_btn.setEnabled(True)
        
        self.sql_text.setPlainText(sql)
        
        attempts = metadata.get("attempts", 1)
        status = metadata.get("final_status", "unknown")
        
        if status == "verified_correct":
            self.verification_label.setText(f"Verified correct (attempt {attempts})")
            self.verification_label.setStyleSheet("color: #00ff88; font-size: 10pt; padding: 5px;")
        elif status == "max_retries_reached":
            self.verification_label.setText(f"Max retries reached ({attempts} attempts)")
            self.verification_label.setStyleSheet("color: #ffa500; font-size: 10pt; padding: 5px;")
        else:
            self.verification_label.setText(f"Status: {status}")
            self.verification_label.setStyleSheet("color: #888; font-size: 10pt; padding: 5px;")
        
        if result is not None and not result.empty:
            self.current_df = result
            self.display_results(result)
            self.statusBar().showMessage(f"Retrieved {len(result)} rows")
        elif result is not None and result.empty:
            self.statusBar().showMessage("Query returned no results")
            self.results_table.clear()
            self.results_table.setRowCount(0)
        else:
            self.statusBar().showMessage("Query generated (not executed)")

    def on_query_error(self, error):
        self.progress_bar.hide()
        self.query_btn.setEnabled(True)
        self.verification_label.setText(f"Error: {error}")
        self.verification_label.setStyleSheet("color: #ff4444; font-size: 10pt; padding: 5px;")
        self.statusBar().showMessage("Query failed")
        QMessageBox.critical(self, "Query Error", str(error))

    def display_results(self, df):
        self.results_table.clear()
        self.results_table.setRowCount(len(df))
        self.results_table.setColumnCount(len(df.columns))
        self.results_table.setHorizontalHeaderLabels(df.columns.tolist())

        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = str(df.iloc[i, j])
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(i, j, item)

        self.results_table.resizeColumnsToContents()

    def export_results(self, format_type):
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
                self.statusBar().showMessage(f"Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    def clear_all(self):
        self.input_text.clear()
        self.sql_text.clear()
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.current_df = None
        self.verification_label.setText("")
        self.statusBar().showMessage("Cleared")

    def closeEvent(self, event):
        if self.db:
            self.db.close()
        event.accept()


def main(remote_server_url=None):
    app = QApplication(sys.argv)

    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(102, 126, 234))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow(remote_server_url=remote_server_url)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
