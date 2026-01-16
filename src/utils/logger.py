import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class AppLogger:

    VERBOSE = logging.DEBUG - 5
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        self._logger = logging.getLogger("NL2SQL_App")
        self._logger.setLevel(logging.DEBUG)

        self._logger.handlers.clear()

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

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
        self._logger.info("=" * 80)
        self._logger.info("Application Logger Initialized")
        self._logger.info(f"Log file: {log_file}")
        self._logger.info("=" * 80)

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

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        if exc_info:
            self._logger.error(message, exc_info=True)
        else:
            self._logger.error(message)

    def critical(self, message: str):
        self._logger.critical(message)

    def separator(self, char: str = "=", length: int = 80):
        self._logger.info(char * length)

    def section(self, title: str):
        self.separator()
        self._logger.info(f"  {title}")
        self.separator()

    def query_log(self, nl_query: str, sql_query: str, success: bool = True):
        status = "[OK]" if success else "[FAIL]"
        self.i("QUERY", f"{status} NL: '{nl_query}'")
        self.d("QUERY", f"   SQL: {sql_query}")

    def db_log(self, operation: str, details: str, success: bool = True):
        status = "[OK]" if success else "[FAIL]"
        self.i("DATABASE", f"{status} {operation}: {details}")

    def gui_log(self, component: str, action: str):
        self.d("GUI", f"{component} - {action}")


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
    print(f"\n[OK] Log file created: {logger.log_file}")
