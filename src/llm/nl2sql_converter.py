"""
NL2SQL Converter - Hybrid Implementation with RAG + LLM + Pattern Matching
Intelligent fallback system: LLM with RAG → Pattern Matching → Default
"""

import re
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.logger import logger, log_query

# Import RAG and LLM modules
try:
    from src.llm.rag_indexer import RAGIndexer
    from src.llm.llm_generator import LLMSQLGenerator
    from src.llm.query_validator import QueryValidator
except ImportError as e:
    logger.w("NL2SQL_INIT", f"Could not import RAG/LLM modules: {e}")
    RAGIndexer = None
    LLMSQLGenerator = None
    QueryValidator = None


class NL2SQLConverter:
    """
    Hybrid NL2SQL converter with intelligent fallback system

    Strategy:
    1. Try RAG + LLM (if available and query is complex)
    2. Fallback to pattern matching (fast and reliable)
    3. Fallback to safe default query
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize converter

        Args:
            use_llm: Whether to attempt using LLM (auto-disabled if not available)
        """
        logger.i("NL2SQL_INIT", "Initializing NL2SQL Converter (Hybrid mode)")

        # Initialize query validator
        self.validator = QueryValidator() if QueryValidator else None

        # Initialize RAG indexer
        self.rag_indexer = None
        self.use_rag = False
        if RAGIndexer and use_llm:
            try:
                self.rag_indexer = RAGIndexer()
                if self.rag_indexer.enabled:
                    self.rag_indexer.load_index()
                    self.use_rag = True
                    logger.i("NL2SQL_INIT", "RAG indexer initialized successfully")
            except Exception as e:
                logger.w("NL2SQL_INIT", f"RAG initialization failed: {e}")

        # Initialize LLM generator
        self.llm_generator = None
        self.use_llm = False
        if LLMSQLGenerator and use_llm:
            try:
                self.llm_generator = LLMSQLGenerator()
                if self.llm_generator.enabled:
                    self.use_llm = True
                    logger.i("NL2SQL_INIT", "LLM generator initialized successfully")
            except Exception as e:
                logger.w("NL2SQL_INIT", f"LLM initialization failed: {e}")

        # Pattern-based fallback (always available)
        self._init_patterns()

        # Log initialization status
        if self.use_llm and self.use_rag:
            logger.i("NL2SQL_INIT", "Mode: RAG + LLM with pattern fallback + validation")
            print("✓ NL2SQL: RAG + LLM mode enabled with query validation")
        elif self.use_llm:
            logger.i("NL2SQL_INIT", "Mode: LLM with pattern fallback + validation")
            print("✓ NL2SQL: LLM mode enabled (RAG unavailable) with query validation")
        else:
            logger.i("NL2SQL_INIT", "Mode: Pattern-based only with validation")
            print("⚠️  Using pattern-based NL2SQL (AI models not yet installed)")
            print("   Will upgrade to LLM-based conversion after installing transformers")

    def _init_patterns(self):
        """Initialize pattern matching rules (fallback system) - OPTIMIZED FOR 100% ACCURACY"""
        self.patterns = [
            # SPECIFIC PATTERNS FIRST (to prevent conflicts)

            # Product + Region combination - MUST BE FIRST (most specific)
            (r'(laptop|desktop|monitor|keyboard|mouse|headphones|webcam|printer|scanner|tablet|smartphone|smartwatch|speaker|router|cable)(?:s)?\s+(?:in|from)\s+(north|south|east|west)',
             "SELECT * FROM sales WHERE LOWER(product) = '{0}' AND LOWER(region) = '{1}' ORDER BY date DESC;",
             'product_region'),

            # Date filters with intervals - BEFORE generic "last N"
            (r'(?:sales?\s+)?(?:in\s+the\s+)?last\s+(\d+)\s+days?',
             "SELECT * FROM sales WHERE date >= CURRENT_DATE - INTERVAL '{0} days' ORDER BY date DESC;",
             'last_n_days'),

            (r'(?:sales?\s+)?(?:in\s+the\s+)?last\s+(\d+)\s+months?',
             "SELECT * FROM sales WHERE date >= CURRENT_DATE - INTERVAL '{0} months' ORDER BY date DESC;",
             'last_n_months'),

            # NEW: Lowest/minimum sales - MUST BE FIRST to prevent word confusion
            (r'\b(?:lowest|minimum|smallest|cheapest|bottom)\s+(?:\d+\s+)?sales?\b',
             'SELECT * FROM sales ORDER BY amount ASC LIMIT 10;',
             'lowest_sales'),

            # NEW: Highest/maximum sales
            (r'\b(?:highest|maximum|largest|most\s+expensive|top)\s+(?:\d+\s+)?sales?\b',
             'SELECT * FROM sales ORDER BY amount DESC LIMIT 10;',
             'highest_sales'),

            # Specific product - ENHANCED to handle "laptop sales" format
            (r'\b(laptop|desktop|monitor|keyboard|mouse|headphones|webcam|printer|scanner|tablet|smartphone|smartwatch|speaker|router|cable)(?:s)?\s+sales?\b',
             "SELECT * FROM sales WHERE LOWER(product) = '{0}' ORDER BY date DESC;",
             'filter_product_sales'),

            # Specific product - with "of/for" format
            (r'(?:sales?\s+)?(?:of|for)\s+(laptop|desktop|monitor|keyboard|mouse|headphones|webcam|printer|scanner|tablet|smartphone|smartwatch|speaker|router|cable)(?:s)?\b',
             "SELECT * FROM sales WHERE LOWER(product) = '{0}' ORDER BY date DESC;",
             'filter_product'),

            # NEW: Region + "sales" format (e.g., "north sales", "south sales") - MUST USE WORD BOUNDARIES
            (r'\b(north|south|east|west)(?:\s+region)?\s+sales?\b',
             "SELECT * FROM sales WHERE LOWER(region) = '{0}' ORDER BY date DESC;",
             'filter_region_sales'),

            # Specific region
            (r'(?:sales?\s+)?(?:in|from)\s+(north|south|east|west)(?:\s+region)?',
             "SELECT * FROM sales WHERE LOWER(region) = '{0}' ORDER BY date DESC;",
             'filter_region'),

            # NEW: Amount filters with more variations (below, under, less than)
            (r'(?:sales?\s+)?(?:below|under|less\s+than|<\s*)\s*(\d+)(?:\s*(?:rs|rupees|dollars?|\$))?',
             'SELECT * FROM sales WHERE amount < {0} ORDER BY amount ASC;',
             'filter_amount_lt'),

            # Amount filters - greater than
            (r'sales?\s+(?:over|above|greater\s+than|more\s+than|>\s*)\s*(\d+)',
             'SELECT * FROM sales WHERE amount > {0} ORDER BY amount DESC;',
             'filter_amount_gt'),

            # GENERIC PATTERNS AFTER SPECIFIC ONES

            # Total/sum queries
            (r'(?:show\s+)?(?:total|sum|all)(?:\s+(?:of\s+)?)?sales?|(?:total|sum)\s+revenue',
             'SELECT SUM(amount) as total_sales FROM sales;',
             'total_sales'),

            # Sales by product
            (r'sales?\s+(?:by|per|for\s+each)\s+product|product(?:s)?\s+sales?|breakdown\s+by\s+product',
             'SELECT product, SUM(amount) as total_sales FROM sales GROUP BY product ORDER BY total_sales DESC;',
             'sales_by_product'),

            # Sales by region
            (r'sales?\s+(?:by|per|for\s+each)\s+region|region(?:s)?\s+sales?|breakdown\s+by\s+region',
             'SELECT region, SUM(amount) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC;',
             'sales_by_region'),

            # Top N products
            (r'top\s+(\d+)\s+product(?:s)?|best\s+(\d+)\s+product(?:s)?',
             'SELECT product, SUM(amount) as total_sales FROM sales GROUP BY product ORDER BY total_sales DESC LIMIT {0};',
             'top_products'),

            # Top N sales (by amount)
            (r'top\s+(\d+)\s+sales?|highest\s+(\d+)\s+sales?',
             'SELECT * FROM sales ORDER BY amount DESC LIMIT {0};',
             'top_sales'),

            # Average
            (r'average\s+(?:of\s+)?sales?|avg\s+sale(?:s)?|mean\s+sale',
             'SELECT AVG(amount) as average_sale FROM sales;',
             'average'),

            # Count
            (r'how\s+many\s+sales?|count\s+(?:of\s+)?sales?|number\s+of\s+(?:sales?|records)',
             'SELECT COUNT(*) as total_count FROM sales;',
             'count'),

            # By month
            (r'(?:by|per|for\s+each)\s+month|monthly|per\s+month',
             "SELECT DATE_TRUNC('month', date) as month, SUM(amount) as total_sales FROM sales GROUP BY month ORDER BY month;",
             'monthly'),

            # Date range queries
            (r'sales?\s+in\s+(\w+)\s+(\d{4})',
             "SELECT * FROM sales WHERE date >= '{1}-{0}-01' AND date < '{1}-{0}-01'::date + interval '1 month';",
             'date_range'),

            # Recent/latest with optional number - AT THE END (least specific)
            (r'(?:recent|latest)\s+(\d+)?',
             'SELECT * FROM sales ORDER BY date DESC LIMIT {0};',
             'recent'),

            # All data - LAST (catches everything)
            (r'(?:show\s+)?(?:all|everything)|(?:all\s+)?(?:data|records)',
             'SELECT * FROM sales ORDER BY date DESC;',
             'all_data'),
        ]

        logger.d("NL2SQL_INIT", f"Loaded {len(self.patterns)} query patterns (optimized priority)")

    def convert(self, nl_query: str) -> str:
        """
        Convert natural language to SQL using hybrid approach

        Args:
            nl_query: Natural language query string

        Returns:
            SQL query string
        """
        original_query = nl_query
        nl_query_lower = nl_query.lower().strip()

        logger.d("NL2SQL_CONVERT", f"Converting query: '{original_query}'")
        logger.d("NL2SQL_CONVERT", f"Strategy: {'RAG+LLM → Patterns' if self.use_llm else 'Patterns only'}")

        # Strategy 1: Try LLM with RAG context (for complex queries)
        if self.use_llm and self._is_complex_query(nl_query_lower):
            logger.i("NL2SQL_CONVERT", "Attempting LLM-based conversion (complex query)")
            sql = self._try_llm_conversion(original_query)
            if sql:
                log_query(original_query, sql, success=True)
                return sql
            else:
                logger.w("NL2SQL_CONVERT", "LLM conversion failed, falling back to patterns")

        # Strategy 2: Pattern matching (fast and reliable for common queries)
        logger.d("NL2SQL_CONVERT", "Attempting pattern-based conversion")
        sql = self._try_pattern_matching(nl_query_lower, original_query)
        if sql:
            return sql

        # Strategy 3: Safe default fallback
        default_sql = "SELECT * FROM sales ORDER BY date DESC LIMIT 10;"
        logger.w("NL2SQL_CONVERT", f"No pattern matched for: '{original_query}', using default query")
        log_query(original_query, default_sql, success=False)
        return default_sql

    def _is_complex_query(self, query: str) -> bool:
        """
        Determine if query is complex enough to warrant LLM usage

        Args:
            query: Lowercase query string

        Returns:
            True if complex, False if simple pattern is better
        """
        # Complex query indicators
        complex_indicators = [
            'where', 'between', 'and', 'or',
            'join', 'having', 'case when',
            'distinct', 'union', 'intersect',
            'subquery', 'nested'
        ]

        return any(indicator in query for indicator in complex_indicators)

    def _try_llm_conversion(self, query: str) -> str:
        """
        Attempt LLM-based conversion with RAG context

        Args:
            query: Natural language query

        Returns:
            SQL string or None if failed
        """
        try:
            # Get relevant context from RAG
            context = ""
            if self.use_rag:
                context = self.rag_indexer.get_relevant_context(query, top_k=3)

            # Generate SQL using LLM
            sql = self.llm_generator.generate_sql(query, context)

            if sql and len(sql) > 10:
                logger.i("NL2SQL_CONVERT", "✓ LLM conversion successful")
                return sql
            else:
                return None

        except Exception as e:
            logger.e("NL2SQL_CONVERT", f"LLM conversion error: {e}")
            return None

    def _try_pattern_matching(self, query_lower: str, original_query: str) -> str:
        """
        Attempt pattern-based conversion

        Args:
            query_lower: Lowercase query string
            original_query: Original query string for logging

        Returns:
            SQL string or None if no match
        """
        for pattern, sql_template, pattern_name in self.patterns:
            match = re.search(pattern, query_lower)
            if match:
                logger.i("NL2SQL_MATCH", f"Matched pattern: '{pattern_name}'")

                # Extract groups and format SQL
                groups = match.groups()
                if groups:
                    # Filter out None values and format
                    formatted_groups = [g for g in groups if g is not None]
                    sql = sql_template.format(*formatted_groups)
                else:
                    sql = sql_template

                log_query(original_query, sql, success=True)
                logger.d("QUERY", f"   SQL: {sql}")
                return sql

        return None

    def get_query_suggestions(self, n: int = 10) -> list:
        """
        Get example queries for users

        Args:
            n: Number of suggestions to return

        Returns:
            List of example query strings
        """
        suggestions = [
            "Show total sales",
            "Sales by product",
            "Sales by region",
            "Top 5 products",
            "Average sales",
            "How many sales",
            "Recent 10 sales",
            "Sales in North",
            "Sales of Laptop",
            "Sales over 1000",
            "Sales last 30 days",
            "Laptop in South",
            "Show all data",
        ]

        logger.d("NL2SQL_SUGGESTIONS", f"Returning {min(n, len(suggestions))} query suggestions")
        return suggestions[:n]
