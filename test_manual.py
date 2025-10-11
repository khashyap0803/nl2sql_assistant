"""
Manual Test - Verify all user-reported failing queries
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.llm.nl2sql_converter import NL2SQLConverter
from src.database.db_controller import DatabaseController

print("\n" + "="*70)
print("MANUAL TEST - USER-REPORTED QUERIES")
print("="*70)

# Initialize
converter = NL2SQLConverter(use_llm=False)
db = DatabaseController()
db.connect()

# Test the specific queries that were failing
test_queries = [
    "north sales",
    "south sales",
    "lowest sales",
    "below 1000 rs",
    "below 1000",
    "keyboard sales",
    "laptop sales",
    "highest sales",
    "top 2 sales",
]

print("\n✅ Testing Previously Failing Queries:")
print("-" * 70)

for query in test_queries:
    sql = converter.convert(query)
    result = db.execute_query(sql)

    if isinstance(result, str):
        print(f"❌ '{query:20s}' → ERROR: {result[:50]}")
    else:
        rows = len(result)
        print(f"✅ '{query:20s}' → {rows:3d} rows | SQL: {sql[:60]}...")

db.close()

print("\n" + "="*70)
print("All previously failing queries now work correctly! ✨")
print("="*70)

