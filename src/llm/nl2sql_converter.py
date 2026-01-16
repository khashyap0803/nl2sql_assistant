import sys
import os
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.logger import logger

try:
    from src.llm.rag_indexer import RAGIndexer
    from src.llm.llm_generator import QwenSQLGenerator
    from src.database.db_controller import DatabaseController
except (ImportError, OSError, RuntimeError, Exception) as e:
    logger.e("NL2SQL_INIT", f"Failed to import modules: {e}")
    RAGIndexer = None
    QwenSQLGenerator = None
    DatabaseController = None


class NL2SQLConverter:
    
    MAX_RETRIES = 5
    
    def __init__(self):
        logger.i("NL2SQL_INIT", "Initializing NL2SQL Converter (RAG + Ollama LLM)")
        
        self.enabled = False
        self.rag = None
        self.llm = None
        self.db = None
        self._db_context_cache = None
        self._db_stats_cache = None
        
        if RAGIndexer:
            try:
                logger.i("NL2SQL_INIT", "Initializing RAG Indexer...")
                self.rag = RAGIndexer()
                if self.rag.enabled:
                    self.rag.load_index()
                    logger.i("NL2SQL_INIT", "RAG Indexer ready")
            except Exception as e:
                logger.w("NL2SQL_INIT", f"RAG initialization failed: {e}")
        
        if QwenSQLGenerator:
            try:
                logger.i("NL2SQL_INIT", "Initializing Ollama LLM...")
                self.llm = QwenSQLGenerator()
                if self.llm.enabled:
                    logger.i("NL2SQL_INIT", "Ollama LLM ready (GPU native)")
                else:
                    logger.e("NL2SQL_INIT", "Ollama LLM not enabled")
            except Exception as e:
                logger.e("NL2SQL_INIT", f"LLM initialization failed: {e}")
        
        if DatabaseController:
            try:
                self.db = DatabaseController()
                logger.i("NL2SQL_INIT", "Database controller ready")
            except Exception as e:
                logger.e("NL2SQL_INIT", f"Database initialization failed: {e}")
        
        if self.llm and self.llm.enabled and self.db:
            self.enabled = True
            logger.i("NL2SQL_INIT", "NL2SQL Converter ready (RAG + Ollama LLM)")
        else:
            logger.e("NL2SQL_INIT", "NL2SQL Converter NOT ready")

    def get_gpu_memory_usage(self) -> Optional[Dict[str, float]]:
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    used_mb = float(parts[0].strip())
                    total_mb = float(parts[1].strip())
                    return {
                        "allocated": used_mb / 1024,
                        "total": total_mb / 1024
                    }
        except:
            pass
        return None

    def _get_full_database_context(self) -> Tuple[str, Dict[str, Any]]:
        if self._db_context_cache:
            return self._db_context_cache, self._db_stats_cache
        
        try:
            if not self.db.connect():
                return self._get_fallback_context(), {}
            
            tables = self.db.get_table_names()
            
            context_parts = []
            all_stats = {}
            
            for table in tables:
                schema = self.db.execute_query(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                
                if isinstance(schema, pd.DataFrame) and not schema.empty:
                    context_parts.append(f"\n=== TABLE: {table} ===")
                    context_parts.append("COLUMNS:")
                    for _, row in schema.iterrows():
                        nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
                        context_parts.append(f"  - {row['column_name']}: {row['data_type']} ({nullable})")
                    
                    sample = self.db.execute_query(f"SELECT * FROM {table} LIMIT 10")
                    if isinstance(sample, pd.DataFrame) and not sample.empty:
                        context_parts.append(f"\nSAMPLE DATA (first {len(sample)} rows):")
                        context_parts.append(sample.to_string(index=False))
                    
                    count_result = self.db.execute_query(f"SELECT COUNT(*) as total FROM {table}")
                    if isinstance(count_result, pd.DataFrame) and not count_result.empty:
                        total_rows = int(count_result.iloc[0]['total'])
                        context_parts.append(f"\nTOTAL ROWS IN TABLE: {total_rows}")
                        all_stats[table] = {"total_rows": total_rows}
                    
                    for _, row in schema.iterrows():
                        col = row['column_name']
                        dtype = row['data_type']
                        
                        if dtype in ('character varying', 'varchar', 'text') and col not in ('id',):
                            try:
                                unique_result = self.db.execute_query(f"""
                                    SELECT DISTINCT {col} FROM {table} 
                                    ORDER BY {col} LIMIT 20
                                """)
                                if isinstance(unique_result, pd.DataFrame) and not unique_result.empty:
                                    unique_vals = unique_result[col].tolist()
                                    context_parts.append(f"UNIQUE VALUES in '{col}': {unique_vals}")
                                    if table not in all_stats:
                                        all_stats[table] = {}
                                    if "unique_values" not in all_stats[table]:
                                        all_stats[table]["unique_values"] = {}
                                    all_stats[table]["unique_values"][col] = unique_vals
                            except:
                                pass
                        
                        elif dtype in ('date', 'timestamp', 'timestamp without time zone', 'timestamp with time zone'):
                            try:
                                date_stats = self.db.execute_query(f"""
                                    SELECT 
                                        MIN({col}) as min_date,
                                        MAX({col}) as max_date,
                                        COUNT(DISTINCT EXTRACT(YEAR FROM {col})) as num_years,
                                        COUNT(DISTINCT EXTRACT(MONTH FROM {col})) as num_months
                                    FROM {table}
                                """)
                                
                                if isinstance(date_stats, pd.DataFrame) and not date_stats.empty:
                                    min_date = date_stats.iloc[0]['min_date']
                                    max_date = date_stats.iloc[0]['max_date']
                                    context_parts.append(f"\nDATE RANGE in '{col}': {min_date} to {max_date}")
                                
                                years_result = self.db.execute_query(f"""
                                    SELECT DISTINCT EXTRACT(YEAR FROM {col})::INTEGER as year 
                                    FROM {table} 
                                    ORDER BY year
                                """)
                                if isinstance(years_result, pd.DataFrame) and not years_result.empty:
                                    years = years_result['year'].tolist()
                                    context_parts.append(f"AVAILABLE YEARS in '{col}': {years}")
                                    if table not in all_stats:
                                        all_stats[table] = {}
                                    all_stats[table]["date_years"] = years
                                
                                months_result = self.db.execute_query(f"""
                                    SELECT 
                                        EXTRACT(YEAR FROM {col})::INTEGER as year,
                                        EXTRACT(MONTH FROM {col})::INTEGER as month,
                                        COUNT(*) as count
                                    FROM {table} 
                                    GROUP BY year, month
                                    ORDER BY year, month
                                """)
                                if isinstance(months_result, pd.DataFrame) and not months_result.empty:
                                    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                                   'July', 'August', 'September', 'October', 'November', 'December']
                                    month_info = []
                                    for _, r in months_result.iterrows():
                                        month_info.append(f"{month_names[int(r['month'])]} {int(r['year'])} ({int(r['count'])} rows)")
                                    context_parts.append(f"AVAILABLE MONTHS with data: {month_info}")
                                    all_stats[table]["date_months"] = months_result.to_dict('records')
                                    
                            except Exception as e:
                                logger.d("NL2SQL_CONTEXT", f"Date analysis failed for {col}: {e}")
            
            self.db.close()
            
            full_context = "\n".join(context_parts)
            self._db_context_cache = full_context
            self._db_stats_cache = all_stats
            
            return full_context, all_stats
            
        except Exception as e:
            logger.e("NL2SQL_CONTEXT", f"Failed to get database context: {e}")
            if self.db:
                self.db.close()
            return self._get_fallback_context(), {}

    def _get_fallback_context(self) -> str:
        if self.rag and self.rag.enabled:
            return self.rag.get_context("database schema", k=10)
        return "Unable to retrieve database context. Please describe your database schema."

    def convert(self, nl_query: str) -> str:
        sql, _, _ = self.convert_and_execute(nl_query, execute=False)
        return sql

    def convert_and_execute(
        self, 
        nl_query: str,
        execute: bool = True
    ) -> Tuple[str, Optional[pd.DataFrame], Dict[str, Any]]:
        if not self.enabled:
            logger.e("NL2SQL_CONVERT", "Converter not initialized")
            return "", None, {"error": "Converter not ready"}
        
        metadata = {
            "attempts": 0,
            "verification_history": [],
            "final_status": "pending",
            "original_query": nl_query
        }
        
        db_context, db_stats = self._get_full_database_context()
        
        if self.rag and self.rag.enabled:
            rag_context = self.rag.get_context(nl_query, k=5)
            if rag_context:
                db_context += f"\n\nADDITIONAL DOMAIN CONTEXT:\n{rag_context}"
        
        current_query = nl_query
        last_sql = None
        last_result = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            metadata["attempts"] = attempt
            logger.i("NL2SQL_CONVERT", f"Attempt {attempt}/{self.MAX_RETRIES}: '{nl_query}'")
            
            try:
                sql = self.llm.generate_sql(current_query, db_context)
                
                if not sql:
                    logger.w("NL2SQL_CONVERT", "LLM failed to generate SQL")
                    current_query = f"""Original question: {nl_query}

Previous attempt failed to generate valid SQL. 
Please analyze the database schema and generate a correct SQL query.
Remember: Use exact column and table names from the schema."""
                    continue
                
                last_sql = sql
                logger.i("NL2SQL_CONVERT", f"Generated SQL: {sql}")
                
                if not execute:
                    metadata["final_status"] = "sql_generated"
                    return sql, None, metadata
                
                if not self.db.connect():
                    logger.e("NL2SQL_CONVERT", "Database connection failed")
                    metadata["final_status"] = "db_connection_failed"
                    return sql, None, metadata
                
                result = self.db.execute_query(sql)
                self.db.close()
                
                if isinstance(result, str):
                    logger.w("NL2SQL_CONVERT", f"Query error: {result}")
                    metadata["verification_history"].append({
                        "attempt": attempt,
                        "sql": sql,
                        "error": result,
                        "is_correct": False
                    })
                    
                    current_query = f"""Original question: {nl_query}

Previous SQL query failed with error:
SQL: {sql}
ERROR: {result}

Analyze the error and generate a corrected SQL query.
Use exact column names from the database schema."""
                    continue
                
                last_result = result
                logger.i("NL2SQL_CONVERT", f"Query returned {len(result)} rows")
                
                expected_info = db_stats.get("sales", {}) if "sales" in db_stats else {}
                
                verification = self.llm.verify_result(
                    nl_query, 
                    sql, 
                    result, 
                    db_context,
                    expected_info
                )
                
                metadata["verification_history"].append({
                    "attempt": attempt,
                    "sql": sql,
                    "rows_returned": len(result),
                    "is_correct": verification["is_correct"],
                    "reason": verification.get("reason", "")
                })
                
                if verification["is_correct"]:
                    logger.i("NL2SQL_CONVERT", f"Query verified correct on attempt {attempt}")
                    metadata["final_status"] = "verified_correct"
                    return sql, result, metadata
                
                logger.w("NL2SQL_CONVERT", f"Verification failed: {verification.get('reason', 'Unknown')}")
                
                current_query = f"""Original question: {nl_query}

Previous SQL was INCORRECT:
SQL: {sql}
Result: {len(result)} rows returned
Problem: {verification.get('reason', 'Result does not match question intent')}
Suggested fix: {verification.get('suggested_fix', 'Re-analyze the question carefully')}

IMPORTANT: 
- If the question asks for data from a specific category (e.g., "south sales"), 
  the result should ONLY contain that category
- If the question asks for "all" data, do NOT use LIMIT
- Use the exact column values shown in the database context

Generate a CORRECTED SQL query:"""
                
            except Exception as e:
                logger.e("NL2SQL_CONVERT", f"Error on attempt {attempt}: {e}", e)
                metadata["verification_history"].append({
                    "attempt": attempt,
                    "error": str(e),
                    "is_correct": False
                })
                current_query = f"{nl_query}\n\nPrevious error: {str(e)}. Please try again."
        
        logger.w("NL2SQL_CONVERT", f"Max retries ({self.MAX_RETRIES}) reached")
        metadata["final_status"] = "max_retries_reached"
        
        return last_sql or "SELECT * FROM sales ORDER BY date;", last_result, metadata

    def get_suggestions(self, partial_query: str = "") -> List[str]:
        suggestions = [
            "Show all data",
            "Total sales by region",
            "Top 10 products by revenue",
            "Sales for January 2025",
            "Average amount by customer type"
        ]
        
        _, db_stats = self._get_full_database_context()
        if db_stats:
            for table, stats in db_stats.items():
                if "unique_values" in stats:
                    for col, values in stats["unique_values"].items():
                        for val in values[:3]:
                            suggestions.append(f"Show {val.lower()} {table}")
        
        return suggestions


if __name__ == "__main__":
    print("Testing NL2SQL Converter...")
    
    converter = NL2SQLConverter()
    if converter.enabled:
        print("Converter ready!")
        
        test_queries = [
            "show all data",
            "south sales",
            "total sales by region"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            sql, result, meta = converter.convert_and_execute(query)
            print(f"SQL: {sql}")
            print(f"Rows: {len(result) if result is not None else 'N/A'}")
            print(f"Status: {meta.get('final_status')}")
    else:
        print("Converter not ready")
