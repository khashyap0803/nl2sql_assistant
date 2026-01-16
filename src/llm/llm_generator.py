import os
import sys
import re
import json
import requests
from typing import Optional, Dict, Any, Tuple
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.logger import logger

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b-instruct-q4_K_M"


class OllamaClient:
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.available = False
        self._check_connection()
    
    def _check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.available = True
                logger.i("OLLAMA", "Connected to Ollama server")
            else:
                logger.e("OLLAMA", f"Ollama returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.e("OLLAMA", "Cannot connect to Ollama - run: ollama serve")
        except Exception as e:
            logger.e("OLLAMA", f"Ollama connection error: {e}")
    
    def generate(
        self, 
        prompt: str, 
        model: str = OLLAMA_MODEL,
        system: str = None,
        temperature: float = 0.1
    ) -> Optional[str]:
        if not self.available:
            return None
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 1024
                }
            }
            
            if system:
                payload["system"] = system
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.e("OLLAMA", f"Generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.e("OLLAMA", f"Generation error: {e}")
            return None
    
    def list_models(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except:
            return []


class QwenSQLGenerator:

    def __init__(self, model_name: str = OLLAMA_MODEL):
        self.model_name = model_name
        self.client = OllamaClient()
        self.enabled = False
        
        if not self.client.available:
            logger.e("LLM_INIT", "Ollama not available - start with: ollama serve")
            return
        
        available_models = self.client.list_models()
        logger.d("LLM_INIT", f"Available models: {available_models}")
        
        model_found = any(model_name in m for m in available_models)
        
        if not model_found:
            logger.i("LLM_INIT", f"Model {model_name} not found, pulling...")
            self._pull_model(model_name)
        
        logger.i("LLM_INIT", f"Using Ollama model: {model_name} (GPU native)")
        self.enabled = True

    def _pull_model(self, model: str) -> bool:
        try:
            logger.i("OLLAMA", f"Pulling model {model}...")
            response = requests.post(
                f"{self.client.base_url}/api/pull",
                json={"name": model},
                timeout=600,
                stream=True
            )
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "status" in data:
                        logger.d("OLLAMA", data["status"])
            logger.i("OLLAMA", f"Model {model} ready")
            return True
        except Exception as e:
            logger.e("OLLAMA", f"Failed to pull model: {e}")
            return False

    def generate_sql(
        self,
        nl_query: str,
        db_context: str
    ) -> Optional[str]:
        if not self.enabled:
            logger.e("LLM_GENERATE", "LLM not enabled")
            return None
        
        try:
            logger.d("LLM_GENERATE", f"Generating SQL for: '{nl_query}'")
            
            system_prompt = """You are an expert SQL query generator. Your task is to convert natural language questions into precise, correct SQL queries.

CRITICAL RULES:
1. ONLY output the SQL query - no explanations, no markdown, no code blocks
2. Analyze the database schema, sample data, and date ranges carefully
3. Match column names and table names EXACTLY as shown in the schema
4. Always end queries with semicolon

INTENT DETECTION - RAW DATA vs AGGREGATION:
When user query contains AGGREGATION keywords use SUM/AVG/COUNT with GROUP BY:
  - "total", "sum", "average", "avg", "count", "how many", "how much"
  - "per", "by each", "for each", "breakdown", "summary"
  - Example: "total south sales" SELECT SUM(amount) FROM sales WHERE region = 'South'

When user query asks for RAW DATA (no aggregation keywords) use SELECT * with WHERE:
  - "[region/category] sales" without "total/sum/count" SELECT * WHERE region = 'X'
  - "[region/category] data" SELECT * WHERE column = 'X'
  - "[region/category] products/customers" SELECT * WHERE column = 'X'
  - "show me", "list", "display", "get" SELECT all matching rows
  - Example: "south sales" SELECT * FROM sales WHERE region = 'South'
  - Example: "north region" SELECT * FROM sales WHERE region = 'North'
  - Example: "business customers" SELECT * FROM sales WHERE customer_type = 'Business'

MULTIPLE VALUES FILTERING:
  - "X and Y sales" or "X or Y" SELECT * WHERE column IN ('X', 'Y')
  - Example: "north and south sales" SELECT * FROM sales WHERE region IN ('North', 'South')
  - Example: "laptop or desktop" SELECT * FROM sales WHERE product IN ('Laptop', 'Desktop')

INTELLIGENT DATE/TIME HANDLING:
- Look at the AVAILABLE YEARS and DATE RANGE in the database context
- If user asks for "January sales" WITHOUT specifying year:
  * Include ALL Januaries from all years
  * Use: WHERE EXTRACT(MONTH FROM date) = 1
- If user asks for "January 2025" (specific year+month):
  * Filter for that exact year AND month
- Month names: January=1, February=2, March=3, April=4, May=5, June=6, July=7, August=8, September=9, October=10, November=11, December=12

SPECIAL PATTERNS:
- "all [items]" SELECT * (no LIMIT, no WHERE)
- "top N" or "best" ORDER BY DESC LIMIT N
- "first quarter" WHERE EXTRACT(MONTH FROM date) IN (1, 2, 3)
- "last month" filter by the latest month in data"""

            prompt = f"""DATABASE CONTEXT:
{db_context}

USER QUESTION: {nl_query}

Generate the SQL query that precisely answers this question. Consider:
1. What data does the user want to see?
2. Should it be filtered? By what criteria?
3. For DATE queries: Check the AVAILABLE YEARS and DATE RANGE above
   - If no year specified, include data from ALL matching periods
   - Use EXTRACT(MONTH FROM date) or EXTRACT(YEAR FROM date) for filtering
4. Should it be aggregated? How?
5. Should it be sorted or limited?

SQL QUERY:"""

            response = self.client.generate(
                prompt=prompt,
                model=self.model_name,
                system=system_prompt,
                temperature=0.1
            )
            
            if not response:
                logger.w("LLM_GENERATE", "No response from Ollama")
                return None
            
            sql = self._extract_sql(response)
            
            if sql:
                logger.i("LLM_GENERATE", f"Generated SQL: {sql[:100]}...")
                return sql
            else:
                logger.w("LLM_GENERATE", "Could not extract valid SQL")
                return None
                
        except Exception as e:
            logger.e("LLM_GENERATE", f"SQL generation failed: {e}", e)
            return None

    def verify_result(
        self,
        nl_query: str,
        sql_query: str,
        result_df: pd.DataFrame,
        db_context: str,
        expected_data_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"is_correct": True, "reason": "LLM not available"}
        
        try:
            logger.d("LLM_VERIFY", f"Verifying result for: '{nl_query}'")
            
            if result_df.empty:
                result_summary = "EMPTY RESULT (0 rows returned)"
            else:
                result_summary = f"""RESULT STATISTICS:
- Total rows returned: {len(result_df)}
- Columns: {list(result_df.columns)}

COMPLETE RESULT DATA:
{result_df.to_string()}"""
            
            expected_info = ""
            if expected_data_info:
                expected_info = f"""
EXPECTED DATA INFO:
- Total rows in table: {expected_data_info.get('total_rows', 'unknown')}
- Unique values in key columns: {expected_data_info.get('unique_values', {})}"""

            prompt = f"""VERIFICATION TASK: Determine if this SQL query and result correctly answer the user's question.

USER QUESTION: {nl_query}

GENERATED SQL: 
{sql_query}

{result_summary}
{expected_info}

DATABASE CONTEXT (for reference):
{db_context}

VERIFICATION CHECKLIST:
1. Does the SQL query correctly interpret the user's question?
2. If user asked for "all" data, are ALL rows returned (no LIMIT)?
3. If filtering by a value (e.g., region, product), is ONLY that value in results?
4. Are the correct columns selected for the question asked?
5. Is aggregation correct if the question implies totals/averages/counts?
6. Does the number of rows returned make logical sense?
7. Look at the actual data - does it match what the question asks for?

BE STRICT: If there's ANY mismatch between question intent and result, mark as INCORRECT.

RESPOND IN EXACTLY THIS FORMAT:
CORRECT: YES or NO
REASON: [One sentence explanation]
FIX: [If incorrect, what SQL change is needed - be specific]"""

            system_prompt = "You are a SQL verification expert. Analyze query results strictly and precisely. Check if the data returned actually answers the user's question correctly."
            
            response = self.client.generate(
                prompt=prompt,
                model=self.model_name,
                system=system_prompt,
                temperature=0.1
            )
            
            if not response:
                return {"is_correct": True, "reason": "Verification unavailable"}
            
            verification = self._parse_verification(response)
            logger.i("LLM_VERIFY", f"Verification: {'CORRECT' if verification['is_correct'] else 'INCORRECT'}")
            
            return verification
            
        except Exception as e:
            logger.e("LLM_VERIFY", f"Verification failed: {e}", e)
            return {"is_correct": True, "reason": f"Verification error: {e}"}

    def _extract_sql(self, response: str) -> Optional[str]:
        text = response.strip()
        
        if "```sql" in text.lower():
            match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()
        elif "```" in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        
        for prefix in ["SQL:", "Query:", "Answer:", "Here is", "The SQL query"]:
            if text.upper().startswith(prefix.upper()):
                text = text[len(prefix):].strip()
        
        if not text.upper().startswith("SELECT") and not text.upper().startswith("WITH"):
            select_match = re.search(r'((?:WITH|SELECT)\s+.*?;)', text, re.DOTALL | re.IGNORECASE)
            if select_match:
                text = select_match.group(1)
            else:
                select_idx = text.upper().find("SELECT")
                if select_idx >= 0:
                    text = text[select_idx:]
                    semi_idx = text.find(";")
                    if semi_idx >= 0:
                        text = text[:semi_idx + 1]
                else:
                    return None
        
        if not text.endswith(';'):
            text += ';'
        
        if len(text) < 10:
            return None
        
        return text

    def _parse_verification(self, response: str) -> Dict[str, Any]:
        result = {
            "is_correct": True,
            "reason": "",
            "suggested_fix": ""
        }
        
        response_upper = response.upper()
        
        if "CORRECT: NO" in response_upper or "CORRECT:NO" in response_upper:
            result["is_correct"] = False
        elif "INCORRECT" in response_upper and "CORRECT: YES" not in response_upper:
            result["is_correct"] = False
        
        reason_match = re.search(r'REASON:\s*(.+?)(?:FIX:|$)', response, re.DOTALL | re.IGNORECASE)
        if reason_match:
            result["reason"] = reason_match.group(1).strip()
        
        fix_match = re.search(r'FIX:\s*(.+?)$', response, re.DOTALL | re.IGNORECASE)
        if fix_match:
            result["suggested_fix"] = fix_match.group(1).strip()
        
        return result


if __name__ == "__main__":
    print("Testing Qwen SQL Generator (Ollama GPU)...")
    
    gen = QwenSQLGenerator()
    if gen.enabled:
        print("LLM Ready!")
        
        context = """
TABLE: sales
COLUMNS:
- id: INTEGER (primary key)
- date: DATE
- amount: DECIMAL
- product: VARCHAR
- region: VARCHAR (values: North, South, East, West)
- quantity: INTEGER
- customer_type: VARCHAR

SAMPLE DATA (5 rows):
id | date       | amount  | product  | region | quantity | customer_type
1  | 2025-01-15 | 1200.50 | Laptop   | North  | 2        | Business
2  | 2025-01-18 | 350.00  | Keyboard | South  | 5        | Regular
3  | 2025-02-01 | 2500.00 | Desktop  | East   | 1        | Premium
4  | 2025-02-10 | 800.00  | Monitor  | West   | 3        | Business
5  | 2025-03-05 | 150.00  | Mouse    | North  | 10       | Regular
"""
        
        sql = gen.generate_sql("show all south region sales", context)
        print(f"Generated SQL: {sql}")
    else:
        print("LLM not available")
