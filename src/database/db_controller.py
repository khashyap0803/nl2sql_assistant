import psycopg2
import pandas as pd
from typing import Union
import sys
import os
from sqlalchemy import create_engine
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import DB_CONFIG
from src.utils.logger import logger, log_db, log_error


class DatabaseController:

    def __init__(self, dbname=None, user=None, password=None, host=None, port=None):
        self.dbname = dbname or DB_CONFIG.get('dbname', 'nl2sql_db')
        self.user = user or DB_CONFIG.get('user', 'postgres')
        self.password = password or DB_CONFIG.get('password', 'postgres')
        self.host = host or DB_CONFIG.get('host', 'localhost')
        self.port = port or DB_CONFIG.get('port', 5432)
        self.conn = None
        self.engine = None

        logger.d("DB_INIT", f"Database controller initialized for {self.dbname}@{self.host}")

    def connect(self):
        try:
            logger.i("DB_CONNECT", f"Attempting connection to {self.dbname}@{self.host}:{self.port}")

            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )

            connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
            self.engine = create_engine(connection_string)

            log_db("Connection", f"Successfully connected to {self.dbname}", success=True)
            print(f"[OK] Connected to database: {self.dbname}")
            return True

        except psycopg2.OperationalError as e:
            log_error("DB_CONNECT", f"Connection failed: {str(e)}", e)
            print(f"[ERROR] Connection failed: {e}")
            print(f"   Make sure PostgreSQL is running and credentials are correct")
            return False
        except Exception as e:
            log_error("DB_CONNECT", f"Unexpected error: {str(e)}", e)
            print(f"[ERROR] Unexpected error: {e}")
            return False

    def execute_query(self, sql: str) -> Union[pd.DataFrame, str]:
        logger.d("DB_QUERY", f"Executing query: {sql[:100]}...")

        try:
            if not self.conn or self.conn.closed:
                logger.w("DB_QUERY", "Connection closed, reconnecting...")
                if not self.connect():
                    error_msg = "Error: Cannot connect to database"
                    log_error("DB_QUERY", error_msg)
                    return error_msg

            df = pd.read_sql_query(sql, self.engine)

            log_db("Query", f"Retrieved {len(df)} rows", success=True)
            logger.d("DB_QUERY", f"Query result: {len(df)} rows, {len(df.columns)} columns")

            return df

        except psycopg2.Error as e:
            error_msg = f"Database Error: {str(e)}"
            log_error("DB_QUERY", error_msg, e)
            return error_msg
        except pd.io.sql.DatabaseError as e:
            error_msg = f"Query Error: {str(e)}"
            log_error("DB_QUERY", error_msg, e)
            return error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            log_error("DB_QUERY", error_msg, e)
            return error_msg

    def execute_sql(self, sql: str) -> bool:
        logger.d("DB_EXEC", f"Executing SQL: {sql[:100]}...")

        try:
            if not self.conn or self.conn.closed:
                if not self.connect():
                    return False

            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
            cursor.close()

            log_db("Execute", "SQL executed successfully", success=True)
            return True

        except Exception as e:
            log_error("DB_EXEC", f"SQL execution error: {str(e)}", e)
            if self.conn:
                self.conn.rollback()
            return False

    def get_table_names(self):
        logger.d("DB_SCHEMA", "Fetching table names")

        sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        result = self.execute_query(sql)
        if isinstance(result, pd.DataFrame):
            tables = result['table_name'].tolist()
            logger.i("DB_SCHEMA", f"Found {len(tables)} tables: {tables}")
            return tables
        return []

    def get_table_schema(self, table_name: str):
        logger.d("DB_SCHEMA", f"Fetching schema for table: {table_name}")

        sql = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """
        result = self.execute_query(sql)

        if isinstance(result, pd.DataFrame) and not result.empty:
            logger.i("DB_SCHEMA", f"Table '{table_name}' has {len(result)} columns")
        else:
            logger.w("DB_SCHEMA", f"Table '{table_name}' not found or has no columns")

        return result

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            log_db("Connection", "Database connection closed", success=True)
            print("[OK] Database connection closed")

    def __del__(self):
        self.close()


def test_connection():
    print("Testing database connection...")
    db = DatabaseController()

    if db.connect():
        result = db.execute_query("SELECT version();")
        if isinstance(result, pd.DataFrame):
            print(f"[OK] PostgreSQL version: {result.iloc[0, 0][:50]}...")

            tables = db.get_table_names()
            print(f"[OK] Tables in database: {tables if tables else 'No tables yet'}")
        else:
            print(f"[ERROR] Query failed: {result}")

        db.close()
        return True
    else:
        print("[ERROR] Connection test failed")
        return False


if __name__ == "__main__":
    test_connection()
