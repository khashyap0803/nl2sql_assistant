import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.llm.nl2sql_converter import NL2SQLConverter
from src.database.db_controller import DatabaseController


class TestCase:
    def __init__(
        self,
        id: int,
        query: str,
        complexity: str,
        expected_keywords: List[str] = None,
        expected_min_rows: int = None,
        expected_max_rows: int = None,
        description: str = ""
    ):
        self.id = id
        self.query = query
        self.complexity = complexity
        self.expected_keywords = expected_keywords or []
        self.expected_min_rows = expected_min_rows
        self.expected_max_rows = expected_max_rows
        self.description = description
        self.result = None
        self.sql = None
        self.rows = None
        self.passed = False
        self.error = None
        self.time_taken = 0


TEST_CASES = [
    TestCase(1, "all", "simple", ["SELECT", "FROM", "sales"], 60, 60, "Get all records"),
    TestCase(2, "show all north region sales", "simple", ["WHERE", "region", "North"], 1, 20, "Filter by North region"),
    TestCase(3, "show all south sales", "simple", ["WHERE", "region", "South"], 1, 20, "Filter by South region"),
    TestCase(4, "show all east region data", "simple", ["WHERE", "region", "East"], 1, 20, "Filter by East region"),
    TestCase(5, "show all west sales", "simple", ["WHERE", "region", "West"], 1, 20, "Filter by West region"),
    TestCase(6, "show all laptop sales", "simple", ["WHERE", "product", "Laptop"], 1, 20, "Filter by product Laptop"),
    TestCase(7, "show all keyboard products", "simple", ["WHERE", "product", "Keyboard"], 1, 20, "Filter by Keyboard"),
    TestCase(8, "show all business customers", "simple", ["WHERE", "customer_type", "Business"], 1, 30, "Filter by Business customer"),
    TestCase(9, "show all premium customers", "simple", ["WHERE", "customer_type", "Premium"], 1, 30, "Filter by Premium customer"),
    TestCase(10, "show all regular customers", "simple", ["WHERE", "customer_type", "Regular"], 1, 30, "Filter by Regular customer"),
    
    TestCase(11, "total sales", "medium", ["SUM", "amount"], 1, 10, "Sum of all sales"),
    TestCase(12, "total sales by region", "medium", ["SUM", "GROUP BY", "region"], 4, 4, "Sum grouped by region"),
    TestCase(13, "average sale amount", "medium", ["AVG", "amount"], 1, 1, "Average sale value"),
    TestCase(14, "count of sales", "medium", ["COUNT"], 1, 1, "Total count of transactions"),
    TestCase(15, "sales by product", "medium", ["GROUP BY", "product"], 5, 15, "Group by product"),
    TestCase(16, "top 5 sales", "medium", ["ORDER BY", "DESC", "LIMIT 5"], 5, 5, "Top 5 highest sales"),
    TestCase(17, "top 10 highest sales", "medium", ["ORDER BY", "DESC", "LIMIT 10"], 10, 10, "Top 10 sales"),
    TestCase(18, "lowest sales", "medium", ["ORDER BY", "ASC", "LIMIT"], 1, 10, "Lowest sale amounts"),
    TestCase(19, "total quantity sold", "medium", ["SUM", "quantity"], 1, 1, "Sum of quantities"),
    TestCase(20, "average quantity per sale", "medium", ["AVG", "quantity"], 1, 1, "Avg quantity"),
    TestCase(21, "sales count by region", "medium", ["COUNT", "GROUP BY", "region"], 4, 4, "Count per region"),
    TestCase(22, "total revenue by product", "medium", ["SUM", "amount", "GROUP BY", "product"], 5, 15, "Revenue per product"),
    TestCase(23, "sales sorted by date", "medium", ["ORDER BY", "date"], 50, 70, "Chronological order"),
    TestCase(24, "latest sales", "medium", ["ORDER BY", "date", "DESC"], 1, 70, "Most recent first"),
    TestCase(25, "earliest sales", "medium", ["ORDER BY", "date", "ASC"], 1, 70, "Oldest first"),
    TestCase(26, "maximum sale amount", "medium", ["MAX", "amount"], 1, 1, "Highest single sale"),
    TestCase(27, "minimum sale amount", "medium", ["MIN", "amount"], 1, 1, "Lowest single sale"),
    TestCase(28, "distinct products", "medium", ["DISTINCT", "product"], 5, 15, "Unique products"),
    TestCase(29, "distinct regions", "medium", ["DISTINCT", "region"], 4, 4, "Unique regions"),
    TestCase(30, "sales by customer type", "medium", ["GROUP BY", "customer_type"], 3, 3, "Group by customer type"),
    
    TestCase(31, "january sales", "complex", ["EXTRACT", "MONTH", "= 1"], 10, 30, "All January data (any year)"),
    TestCase(32, "february sales", "complex", ["EXTRACT", "MONTH", "= 2"], 10, 30, "All February data"),
    TestCase(33, "march sales", "complex", ["EXTRACT", "MONTH", "= 3"], 10, 30, "All March data"),
    TestCase(34, "january 2025", "complex", ["EXTRACT", "YEAR", "2025", "MONTH", "1"], 10, 30, "Jan 2025 specific"),
    TestCase(35, "2025 sales", "complex", ["EXTRACT", "YEAR", "2025"], 50, 70, "All 2025 data"),
    TestCase(36, "north region total sales", "complex", ["SUM", "WHERE", "region", "North"], 1, 1, "Total for North"),
    TestCase(37, "south region total sales", "complex", ["SUM", "WHERE", "region", "South"], 1, 1, "Total for South"),
    TestCase(38, "laptop sales in north", "complex", ["WHERE", "product", "Laptop", "AND", "region", "North"], 0, 10, "Product + Region filter"),
    TestCase(39, "business customer sales in east", "complex", ["WHERE", "customer_type", "Business", "AND", "region", "East"], 0, 15, "Customer + Region"),
    TestCase(40, "total sales above 1000", "complex", ["WHERE", "amount", ">", "1000"], 5, 40, "Amount threshold"),
    TestCase(41, "sales between 500 and 1500", "complex", ["WHERE", "amount", "BETWEEN", "500", "1500"], 10, 50, "Amount range"),
    TestCase(42, "show all north and south sales", "complex", ["WHERE", "region", "IN", "North", "South"], 2, 40, "Multiple regions"),
    TestCase(43, "show all laptop or desktop sales", "complex", ["WHERE", "product", "IN", "Laptop", "Desktop"], 2, 25, "Multiple products"),
    TestCase(44, "monthly sales summary", "complex", ["SUM", "GROUP BY"], 3, 12, "Monthly aggregation"),
    TestCase(45, "quarterly sales", "complex", ["SUM", "GROUP BY"], 1, 5, "Quarterly summary"),
    TestCase(46, "weekly revenue", "complex", ["SUM", "GROUP BY"], 5, 15, "Weekly aggregation"),
    TestCase(47, "sales per day of week", "complex", ["SUM", "GROUP BY"], 1, 7, "By day of week"),
    TestCase(48, "first quarter results", "complex", ["WHERE", "MONTH"], 1, 70, "Q1 filter"),
    TestCase(49, "march sales data", "complex", ["WHERE", "MONTH", "3"], 10, 30, "March data"),
    TestCase(50, "year to date sales", "complex", ["SUM"], 1, 5, "YTD total"),
    
    TestCase(51, "show me the total revenue for each product in the north region sorted by revenue descending", "highly_complex",
             ["SUM", "amount", "GROUP BY", "product", "WHERE", "region", "North", "ORDER BY", "DESC"], 1, 15,
             "Product revenue in North, sorted"),
    TestCase(52, "what is the average sale amount per region and customer type", "highly_complex",
             ["AVG", "amount", "GROUP BY", "region", "customer_type"], 8, 15,
             "Two-level grouping"),
    TestCase(53, "show sales comparison between north and south regions by month", "highly_complex",
             ["EXTRACT", "MONTH", "region", "IN", "North", "South", "GROUP BY"], 2, 30,
             "Regional monthly comparison"),
    TestCase(54, "find the top selling product in each region with total quantity", "highly_complex",
             ["SUM", "quantity", "GROUP BY", "region", "product", "ORDER BY"], 5, 50,
             "Top product per region"),
    TestCase(55, "calculate percentage contribution of each region to total sales", "highly_complex",
             ["SUM", "amount", "GROUP BY", "region"], 4, 4,
             "Percentage calculation"),
    TestCase(56, "show month over month growth in sales", "highly_complex",
             ["EXTRACT", "MONTH", "SUM", "ORDER BY"], 2, 12,
             "MoM growth analysis"),
    TestCase(57, "identify the best performing product by average sale amount", "highly_complex",
             ["AVG", "amount", "GROUP BY", "product", "ORDER BY", "DESC", "LIMIT 1"], 1, 1,
             "Best product by avg"),
    TestCase(58, "show cumulative sales over time", "highly_complex",
             ["SUM", "ORDER BY", "date"], 10, 70,
             "Running total"),
    TestCase(59, "find all sales where quantity is above average", "highly_complex",
             ["WHERE", "quantity", ">", "AVG"], 10, 40,
             "Above average filter"),
    TestCase(60, "show the distribution of sales across customer types for each product", "highly_complex",
             ["GROUP BY", "product", "customer_type", "COUNT"], 15, 45,
             "Distribution matrix"),
    TestCase(61, "compare january and february sales by product", "highly_complex",
             ["EXTRACT", "MONTH", "IN", "1", "2", "GROUP BY", "product"], 10, 30,
             "Monthly product comparison"),
    TestCase(62, "show daily sales trend for the north region", "highly_complex",
             ["WHERE", "region", "North", "GROUP BY", "date", "ORDER BY", "date"], 5, 30,
             "Daily trend for region"),
    TestCase(63, "find products with sales in all four regions", "highly_complex",
             ["GROUP BY", "product"], 0, 30,
             "Multi-region products"),
    TestCase(64, "calculate the average basket size by customer type and region", "highly_complex",
             ["AVG", "GROUP BY"], 8, 15,
             "Basket size analysis"),
    TestCase(65, "show the busiest sales day based on transaction count", "highly_complex",
             ["COUNT", "GROUP BY", "date", "ORDER BY"], 1, 5,
             "Busiest day"),
    TestCase(66, "find products that have never been sold in the west region", "highly_complex",
             ["WHERE", "region"], 0, 15,
             "Exclusion query"),
    TestCase(67, "show sales performance of each region compared to the overall average", "highly_complex",
             ["AVG", "GROUP BY", "region"], 4, 4,
             "Against average"),
    TestCase(68, "calculate the rolling 3-day average of sales", "highly_complex",
             ["AVG", "OVER", "ORDER BY", "date"], 10, 70,
             "Rolling average"),
    TestCase(69, "show the rank of each product by total sales amount", "highly_complex",
             ["SUM", "amount", "GROUP BY", "product", "ORDER BY", "DESC"], 5, 15,
             "Product ranking"),
    TestCase(70, "find the month with the highest average sale amount", "highly_complex",
             ["AVG", "amount", "EXTRACT", "MONTH", "GROUP BY", "ORDER BY", "DESC", "LIMIT 1"], 1, 1,
             "Best month by avg"),
    TestCase(71, "show premium customers who made purchases above 2000 in the north region", "highly_complex",
             ["WHERE", "customer_type", "Premium", "AND", "amount", ">", "2000", "AND", "region", "North"], 0, 10,
             "Multi-filter premium"),
    TestCase(72, "calculate year over year growth rate for each region", "highly_complex",
             ["EXTRACT", "YEAR", "SUM", "GROUP BY", "region"], 4, 10,
             "YoY by region"),
    TestCase(73, "find the most popular product by sales count", "highly_complex",
             ["GROUP BY", "product", "COUNT", "ORDER BY", "DESC"], 1, 15,
             "Popular products"),
    TestCase(74, "show the sales funnel by customer type from highest to lowest", "highly_complex",
             ["SUM", "amount", "GROUP BY", "customer_type", "ORDER BY", "DESC"], 3, 3,
             "Customer funnel"),
    TestCase(75, "identify outliers with sales amount more than 3 standard deviations from mean", "highly_complex",
             ["STDDEV", "AVG", "WHERE", "amount", ">"], 0, 10,
             "Statistical outliers"),
    TestCase(76, "show the percentage of sales each day represents", "highly_complex",
             ["SUM", "GROUP BY"], 20, 70,
             "Daily percentage"),
    TestCase(77, "compare business vs premium customer spending in each region", "highly_complex",
             ["WHERE", "customer_type", "IN", "Business", "Premium", "GROUP BY", "region"], 4, 10,
             "Customer comparison"),
    TestCase(78, "find products that had sales above 1000 in every month", "highly_complex",
             ["HAVING", "COUNT", "EXTRACT", "MONTH", "GROUP BY", "product"], 0, 15,
             "Consistent performers"),
    TestCase(79, "show the median sale amount for each region", "highly_complex",
             ["PERCENTILE_CONT", "0.5", "GROUP BY", "region"], 4, 4,
             "Median by region"),
    TestCase(80, "calculate the coefficient of variation for sales by product", "highly_complex",
             ["STDDEV", "AVG", "GROUP BY", "product"], 5, 15,
             "CV analysis"),
    TestCase(81, "show sales trends month over month by product", "highly_complex",
             ["SUM", "GROUP BY", "product"], 5, 50,
             "MoM trends"),
    TestCase(82, "find the correlation between quantity and total amount by product", "highly_complex",
             ["CORR", "quantity", "amount", "GROUP BY", "product"], 1, 15,
             "Correlation analysis"),
    TestCase(83, "show the moving sum of sales for the last 7 days", "highly_complex",
             ["SUM", "OVER", "ROWS", "BETWEEN", "PRECEDING"], 10, 70,
             "Moving sum"),
    TestCase(84, "identify seasonal patterns in sales data", "highly_complex",
             ["EXTRACT", "MONTH", "AVG", "amount", "GROUP BY", "ORDER BY"], 3, 12,
             "Seasonality"),
    TestCase(85, "calculate the pareto analysis of products", "highly_complex",
             ["SUM", "amount", "GROUP BY", "product", "ORDER BY", "DESC"], 5, 15,
             "Pareto 80/20"),
    TestCase(86, "show customer acquisition trend by month and type", "highly_complex",
             ["EXTRACT", "MONTH", "COUNT", "DISTINCT", "GROUP BY", "customer_type"], 5, 36,
             "Acquisition trend"),
    TestCase(87, "find the highest sale in each region", "highly_complex",
             ["MAX", "GROUP BY", "region", "ORDER BY"], 4, 10,
             "Highest per region"),
    TestCase(88, "calculate the weighted average sale amount by region", "highly_complex",
             ["SUM", "amount", "quantity", "GROUP BY", "region"], 4, 4,
             "Weighted average"),
    TestCase(89, "show all combinations of product and region with their totals", "highly_complex",
             ["SUM", "amount", "GROUP BY", "product", "region", "ORDER BY"], 20, 60,
             "Cross-tab analysis"),
    TestCase(90, "find the break-even point for sales amounts", "highly_complex",
             ["AVG", "SUM", "amount"], 1, 10,
             "Break-even"),
    TestCase(91, "show the contribution margin by product category", "highly_complex",
             ["SUM", "amount", "GROUP BY", "product", "ORDER BY"], 5, 15,
             "Contribution margin"),
    TestCase(92, "calculate the churn rate based on decreasing monthly purchases", "highly_complex",
             ["COUNT", "EXTRACT", "MONTH", "GROUP BY"], 1, 12,
             "Churn analysis"),
    TestCase(93, "show sales distribution by first month", "highly_complex",
             ["GROUP BY", "SUM", "ORDER BY"], 1, 15,
             "Cohort analysis"),
    TestCase(94, "show total days of sales per product", "highly_complex",
             ["COUNT", "GROUP BY", "product"], 1, 15,
             "Sales days per product"),
    TestCase(95, "show the distribution of sale amounts", "highly_complex",
             ["amount", "COUNT", "GROUP BY", "ORDER BY"], 5, 70,
             "Frequency distribution"),
    TestCase(96, "calculate the exponential moving average of sales", "highly_complex",
             ["AVG", "OVER", "ROWS", "BETWEEN"], 10, 70,
             "EMA calculation"),
    TestCase(97, "show the z-score normalized sales by region", "highly_complex",
             ["STDDEV", "AVG", "amount", "GROUP BY", "region"], 4, 4,
             "Z-score normalization"),
    TestCase(98, "find products with statistically significant sales differences between regions", "highly_complex",
             ["AVG", "STDDEV", "GROUP BY", "product", "region"], 20, 60,
             "Statistical significance"),
    TestCase(99, "calculate the geometric mean of sales amounts", "highly_complex",
             ["EXP", "AVG", "LN", "amount"], 1, 15,
             "Geometric mean"),
    TestCase(100, "show the complete sales analysis report with all key metrics by region product and month", "highly_complex",
              ["SUM", "AVG", "COUNT", "GROUP BY", "region", "product", "EXTRACT", "MONTH", "ORDER BY"], 30, 200,
              "Complete analysis"),
]


class NL2SQLTestRunner:
    
    def __init__(self):
        print("=" * 80)
        print("NL2SQL COMPREHENSIVE TEST SUITE - 100 TEST CASES")
        print("=" * 80)
        print()
        
        self.converter = None
        self.db = None
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "by_complexity": {
                "simple": {"total": 0, "passed": 0},
                "medium": {"total": 0, "passed": 0},
                "complex": {"total": 0, "passed": 0},
                "highly_complex": {"total": 0, "passed": 0}
            }
        }
    
    def setup(self) -> bool:
        try:
            print("Initializing NL2SQL Converter...")
            self.converter = NL2SQLConverter()
            if not self.converter.enabled:
                print("[ERROR] Converter not enabled!")
                return False
            
            print("Initializing Database Controller...")
            self.db = DatabaseController()
            if not self.db.connect():
                print("[ERROR] Database connection failed!")
                return False
            self.db.close()
            
            print("[OK] Setup complete\n")
            return True
            
        except Exception as e:
            print(f"[ERROR] Setup failed: {e}")
            return False
    
    def run_test(self, test: TestCase) -> bool:
        try:
            start_time = time.time()
            
            sql, result, metadata = self.converter.convert_and_execute(test.query)
            
            test.time_taken = time.time() - start_time
            test.sql = sql
            
            if sql is None:
                test.error = "No SQL generated"
                return False
            
            if result is None:
                test.error = "No result returned"
                return False
            
            test.rows = len(result)
            
            sql_upper = sql.upper()
            missing_keywords = []
            for keyword in test.expected_keywords:
                if keyword.upper() not in sql_upper:
                    missing_keywords.append(keyword)
            
            row_check = True
            if test.expected_min_rows is not None and test.rows < test.expected_min_rows:
                row_check = False
            if test.expected_max_rows is not None and test.rows > test.expected_max_rows:
                row_check = False
            
            keywords_found = len(test.expected_keywords) - len(missing_keywords)
            keyword_ratio = keywords_found / max(len(test.expected_keywords), 1)
            
            test.passed = keyword_ratio >= 0.5 and row_check
            
            if not test.passed:
                if missing_keywords:
                    test.error = f"Missing: {missing_keywords}, Rows: {test.rows}"
                else:
                    test.error = f"Row check failed: got {test.rows}, expected {test.expected_min_rows}-{test.expected_max_rows}"
            
            return test.passed
            
        except Exception as e:
            test.error = str(e)
            test.time_taken = time.time() - start_time
            return False
    
    def run_all(self):
        if not self.setup():
            return
        
        print(f"Running {len(TEST_CASES)} test cases...\n")
        print("-" * 80)
        
        for test in TEST_CASES:
            self.results["total"] += 1
            self.results["by_complexity"][test.complexity]["total"] += 1
            
            print(f"Test {test.id:3d} [{test.complexity:15s}]: {test.query[:50]:50s}...", end=" ")
            
            passed = self.run_test(test)
            
            if passed:
                self.results["passed"] += 1
                self.results["by_complexity"][test.complexity]["passed"] += 1
                print(f"[PASS] ({test.rows} rows, {test.time_taken:.2f}s)")
            else:
                if test.error:
                    self.results["errors"] += 1
                else:
                    self.results["failed"] += 1
                print(f"[FAIL] {test.error or 'Unexpected result'}")
        
        print("-" * 80)
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        errors = self.results["errors"]
        
        print(f"\nOVERALL: {passed}/{total} passed ({100*passed/total:.1f}%)")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Errors: {errors}")
        
        print("\nBY COMPLEXITY:")
        for complexity, stats in self.results["by_complexity"].items():
            if stats["total"] > 0:
                pct = 100 * stats["passed"] / stats["total"]
                print(f"  {complexity:15s}: {stats['passed']:3d}/{stats['total']:3d} ({pct:.1f}%)")
        
        print("\n" + "=" * 80)
    
    def save_results(self):
        output = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.results,
            "tests": []
        }
        
        for test in TEST_CASES:
            output["tests"].append({
                "id": test.id,
                "query": test.query,
                "complexity": test.complexity,
                "description": test.description,
                "passed": test.passed,
                "sql": test.sql,
                "rows": test.rows,
                "time_taken": test.time_taken,
                "error": test.error
            })
        
        with open("test_results.json", "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results.json")


def main():
    runner = NL2SQLTestRunner()
    runner.run_all()


if __name__ == "__main__":
    main()
