"""
Test Script - Comprehensive testing of improved NL2SQL system
Tests pattern matching, validation, and database queries
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.database.db_controller import DatabaseController
from src.llm.nl2sql_converter import NL2SQLConverter
from config import DB_CONFIG

def test_database_connection():
    """Test database connectivity"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)

    db = DatabaseController()
    if db.connect():
        print("✅ Database connection successful")

        # Test query
        result = db.execute_query("SELECT COUNT(*) as count FROM sales")
        if isinstance(result, str):
            print(f"❌ Query failed: {result}")
            return False
        else:
            count = result['count'].iloc[0]
            print(f"✅ Database has {count} sales records")
            db.close()
            return True
    else:
        print("❌ Database connection failed")
        return False

def test_expanded_patterns():
    """Test all query patterns"""
    print("\n" + "="*60)
    print("TEST 2: Expanded Pattern Matching (23+ patterns)")
    print("="*60)

    # Initialize converter
    converter = NL2SQLConverter(use_llm=False)

    # Test queries covering all patterns - UPDATED WITH NEW PATTERNS
    test_queries = [
        # Basic patterns (1-9)
        ("Show total sales", "sum(amount)", "total_sales"),
        ("Sales by product", "group by product", "sales_by_product"),
        ("Sales by region", "group by region", "sales_by_region"),
        ("Top 5 products", "limit 5", "top_products"),
        ("Average sales", "avg(amount)", "average"),
        ("How many sales", "count(*)", "count"),
        ("Sales by month", "date_trunc", "monthly"),
        ("Recent 10", "order by date desc limit", "recent"),
        ("Show all data", "select * from sales", "all_data"),

        # Region/Product filters (10-12)
        ("Sales in North", "region", "filter_region"),
        ("Sales of Laptop", "product", "filter_product"),
        ("Laptop sales", "product", "filter_product_sales"),

        # NEW: Region sales format (13-14)
        ("North sales", "region", "filter_region_sales"),
        ("South sales", "region", "filter_region_sales"),

        # Amount filters (15-18)
        ("Sales over 1000", "amount > 1000", "filter_amount_gt"),
        ("Sales under 500", "amount < 500", "filter_amount_lt"),
        ("Below 1000 rs", "amount < 1000", "filter_amount_lt"),  # NEW with currency
        ("Below 2000", "amount < 2000", "filter_amount_lt"),

        # NEW: Lowest/Highest sales (19-20)
        ("Lowest sales", "order by amount asc", "lowest_sales"),
        ("Highest sales", "order by amount desc", "highest_sales"),

        # Date filters (21-22)
        ("Sales last 30 days", "interval '30 days'", "last_n_days"),
        ("Sales last 3 months", "interval '3 months'", "last_n_months"),

        # Combined filters (23-24)
        ("Laptop in North", "product", "product_region"),
        ("Smartphone in East", "product", "product_region"),
    ]

    passed = 0
    failed = 0

    for i, (query, expected_fragment, pattern_name) in enumerate(test_queries, 1):
        sql = converter.convert(query)

        # Check if expected fragment is in SQL (case-insensitive)
        if expected_fragment.lower() in sql.lower():
            print(f"  ✅ Test {i:2d}: '{query:30s}' → {pattern_name}")
            passed += 1
        else:
            print(f"  ❌ Test {i:2d}: '{query:30s}' → Failed")
            print(f"           Expected fragment: {expected_fragment}")
            print(f"           Got: {sql[:80]}")
            failed += 1

    accuracy = passed/(passed+failed)*100
    print(f"\n  Results: {passed} passed, {failed} failed ({accuracy:.1f}% accuracy)")

    # Success if 90%+ accuracy
    return accuracy >= 90.0

def test_query_execution():
    """Test actual query execution with validation"""
    print("\n" + "="*60)
    print("TEST 3: Query Execution with Validation")
    print("="*60)

    db = DatabaseController()
    if not db.connect():
        print("❌ Cannot connect to database")
        return False

    converter = NL2SQLConverter(use_llm=False)

    # Test queries
    test_queries = [
        "Show total sales",
        "Sales by product",
        "Top 5 products",
        "Sales in North",
        "Sales over 1000",
        "Laptop in South",
    ]

    passed = 0
    for query in test_queries:
        sql = converter.convert(query)
        result = db.execute_query(sql)

        if isinstance(result, str):
            print(f"  ❌ '{query}' → Error: {result[:50]}")
        else:
            print(f"  ✅ '{query}' → {len(result)} rows")

            # Validate if validator is available
            if converter.validator:
                validation = converter.validator.validate_query_result(query, sql, result)
                if validation['warnings']:
                    print(f"     ⚠️ Warnings: {', '.join(validation['warnings'][:2])}")
                print(f"     📊 Confidence: {validation['confidence']:.1%}")

            passed += 1

    db.close()
    print(f"\n  Results: {passed}/{len(test_queries)} queries executed successfully")
    return passed == len(test_queries)

def test_database_statistics():
    """Show database statistics"""
    print("\n" + "="*60)
    print("TEST 4: Database Statistics")
    print("="*60)

    db = DatabaseController()
    if not db.connect():
        return False

    # Total sales
    result = db.execute_query("SELECT SUM(amount) as total, AVG(amount) as avg, COUNT(*) as count FROM sales")
    if not isinstance(result, str):
        total = result['total'].iloc[0]
        avg = result['avg'].iloc[0]
        count = result['count'].iloc[0]
        print(f"  📊 Total Sales: ${total:,.2f}")
        print(f"  📊 Average Sale: ${avg:,.2f}")
        print(f"  📊 Total Records: {count}")

    # Sales by region
    print("\n  Sales by Region:")
    result = db.execute_query("""
        SELECT region, COUNT(*) as count, SUM(amount) as total
        FROM sales
        GROUP BY region
        ORDER BY total DESC
    """)
    if not isinstance(result, str):
        for _, row in result.iterrows():
            print(f"    {row['region']:10s} - {row['count']:2.0f} sales - ${row['total']:,.2f}")

    # Top products
    print("\n  Top 5 Products:")
    result = db.execute_query("""
        SELECT product, COUNT(*) as count, SUM(amount) as total
        FROM sales
        GROUP BY product
        ORDER BY total DESC
        LIMIT 5
    """)
    if not isinstance(result, str):
        for i, row in result.iterrows():
            print(f"    {i+1}. {row['product']:15s} - {row['count']:2.0f} sales - ${row['total']:,.2f}")

    db.close()
    return True

def test_ai_models():
    """Test AI model installation and functionality"""
    print("\n" + "="*60)
    print("TEST 5: AI Models Installation")
    print("="*60)

    try:
        import torch
        import transformers
        import sentence_transformers
        import faiss

        print(f"  ✅ torch: {torch.__version__}")
        print(f"  ✅ transformers: {transformers.__version__}")
        print(f"  ✅ sentence-transformers: {sentence_transformers.__version__}")
        print(f"  ✅ faiss: {faiss.__version__}")

        # Test if models can be used
        print("\n  Testing AI functionality:")
        converter = NL2SQLConverter(use_llm=True)

        if converter.use_llm:
            print("  ✅ LLM mode available")
        else:
            print("  ⚠️  LLM mode not activated (will activate on first complex query)")

        if converter.use_rag:
            print("  ✅ RAG mode available")
        else:
            print("  ⚠️  RAG mode not activated (will activate on first use)")

        return True

    except ImportError as e:
        print(f"  ❌ AI packages not fully installed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("NL2SQL ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print("\nTesting improvements:")
    print("  ✓ Expanded database (60 records)")
    print("  ✓ 18 query patterns (was 13)")
    print("  ✓ Query validation system")
    print("  ✓ AI models installation")
    print("  ✓ RAG + LLM integration")

    # Run tests
    results = []

    results.append(("Database Connection", test_database_connection()))
    results.append(("Pattern Matching", test_expanded_patterns()))
    results.append(("Query Execution", test_query_execution()))
    results.append(("Database Statistics", test_database_statistics()))
    results.append(("AI Models", test_ai_models()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n  Overall: {total_passed}/{len(results)} tests passed")

    if total_passed == len(results):
        print("\n  🎉 All tests passed! System is production-ready!")
    elif total_passed >= len(results) - 1:
        print("\n  ✅ System is working well! Minor issues detected.")
    else:
        print("\n  ⚠️ Some tests failed. Check output above for details.")

    print("\n" + "="*60)

    return total_passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
