"""
Application Logger - Similar to Android Logcat
Centralized logging system for debugging and monitoring
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class AppLogger:
    """
    Centralized logging system similar to Android Logcat
    Provides different log levels and formatted output
    """

    # Log levels (similar to Android)
    VERBOSE = logging.DEBUG - 5
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    _instance = None

    def __new__(cls):
        """Singleton pattern - only one logger instance"""
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize logger"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create logger
        self._logger = logging.getLogger("NL2SQL_App")
        self._logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self._logger.handlers.clear()

        # Console handler (colored output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File handler (detailed logs)
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

        self.log_file = log_file
        self._logger.info("=" * 80)
        self._logger.info("Application Logger Initialized")
        self._logger.info(f"Log file: {log_file}")
        self._logger.info("=" * 80)

    # Logging methods (similar to Android Log.v, Log.d, Log.i, etc.)
    def v(self, tag: str, message: str):
        """Verbose log (most detailed)"""
        self._logger.log(self.VERBOSE, f"[{tag}] {message}")

    def d(self, tag: str, message: str):
        """Debug log"""
        self._logger.debug(f"[{tag}] {message}")

    def i(self, tag: str, message: str):
        """Info log"""
        self._logger.info(f"[{tag}] {message}")

    def w(self, tag: str, message: str):
        """Warning log"""
        self._logger.warning(f"[{tag}] {message}")

    def e(self, tag: str, message: str, exc_info: Optional[Exception] = None):
        """Error log"""
        if exc_info:
            self._logger.error(f"[{tag}] {message}", exc_info=True)
        else:
            self._logger.error(f"[{tag}] {message}")

    def c(self, tag: str, message: str):
        """Critical log"""
        self._logger.critical(f"[{tag}] {message}")

    # Convenience methods
    def debug(self, message: str):
        """Simple debug message"""
        self._logger.debug(message)

    def info(self, message: str):
        """Simple info message"""
        self._logger.info(message)

    def warning(self, message: str):
        """Simple warning message"""
        self._logger.warning(message)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        """Simple error message"""
        if exc_info:
            self._logger.error(message, exc_info=True)
        else:
            self._logger.error(message)

    def critical(self, message: str):
        """Simple critical message"""
        self._logger.critical(message)

    def separator(self, char: str = "=", length: int = 80):
        """Print separator line"""
        self._logger.info(char * length)

    def section(self, title: str):
        """Print section header"""
        self.separator()
        self._logger.info(f"  {title}")
        self.separator()

    def query_log(self, nl_query: str, sql_query: str, success: bool = True):
        """Special log for query conversions"""
        status = "✓" if success else "✗"
        self.i("QUERY", f"{status} NL: '{nl_query}'")
        self.d("QUERY", f"   SQL: {sql_query}")

    def db_log(self, operation: str, details: str, success: bool = True):
        """Special log for database operations"""
        status = "✓" if success else "✗"
        self.i("DATABASE", f"{status} {operation}: {details}")

    def gui_log(self, component: str, action: str):
        """Special log for GUI events"""
        self.d("GUI", f"{component} - {action}")


# Create global logger instance
logger = AppLogger()


# Convenience functions for quick access
def log_debug(tag: str, message: str):
    """Quick debug log"""
    logger.d(tag, message)

def log_info(tag: str, message: str):
    """Quick info log"""
    logger.i(tag, message)

def log_warning(tag: str, message: str):
    """Quick warning log"""
    logger.w(tag, message)

def log_error(tag: str, message: str, exc: Optional[Exception] = None):
    """Quick error log"""
    logger.e(tag, message, exc)

def log_query(nl_query: str, sql_query: str, success: bool = True):
    """Quick query log"""
    logger.query_log(nl_query, sql_query, success)

def log_db(operation: str, details: str, success: bool = True):
    """Quick database log"""
    logger.db_log(operation, details, success)


# Test function
if __name__ == "__main__":
    logger.section("Logger Test Suite")

    logger.v("TEST", "This is a verbose message")
    logger.d("TEST", "This is a debug message")
    logger.i("TEST", "This is an info message")
    logger.w("TEST", "This is a warning message")
    logger.e("TEST", "This is an error message")
    logger.c("TEST", "This is a critical message")

    logger.separator()

    logger.query_log("show total sales", "SELECT SUM(amount) FROM sales", success=True)
    logger.db_log("Connection", "Connected to nl2sql_db", success=True)
    logger.gui_log("MainWindow", "Query button clicked")

    logger.section("Test Complete")
    print(f"\n✓ Log file created: {logger.log_file}")
