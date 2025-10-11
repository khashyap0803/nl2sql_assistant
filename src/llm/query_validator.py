"""
Query Validator - Validates and verifies SQL query results
Provides semantic validation and result verification
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
import re


class QueryValidator:
    """
    Validates query results for correctness and semantic meaning
    """

    def __init__(self):
        self.validation_history = []

    def validate_query_result(
        self,
        natural_query: str,
        sql_query: str,
        result_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Validate a query result for correctness and semantic accuracy

        Args:
            natural_query: Original natural language query
            sql_query: Generated SQL query
            result_df: Query result as DataFrame

        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': True,
            'confidence': 1.0,
            'warnings': [],
            'suggestions': [],
            'semantic_check': None,
            'data_quality': None
        }

        # Check 1: Empty results
        if result_df.empty:
            validation['warnings'].append("Query returned no results")
            validation['confidence'] *= 0.7
            validation['suggestions'].append(
                "Try broadening your search criteria or check if data exists"
            )

        # Check 2: Semantic validation based on query intent
        semantic_check = self._validate_semantic_meaning(
            natural_query, sql_query, result_df
        )
        validation['semantic_check'] = semantic_check
        validation['confidence'] *= semantic_check['confidence']
        validation['warnings'].extend(semantic_check.get('warnings', []))

        # Check 3: Data quality checks
        data_quality = self._check_data_quality(result_df)
        validation['data_quality'] = data_quality

        # Check 4: SQL query structure validation
        sql_check = self._validate_sql_structure(sql_query, natural_query)
        validation['warnings'].extend(sql_check.get('warnings', []))
        validation['suggestions'].extend(sql_check.get('suggestions', []))

        # Overall validation
        if validation['confidence'] < 0.5:
            validation['is_valid'] = False
            validation['warnings'].append("Low confidence in query results")

        # Store in history
        self.validation_history.append({
            'natural_query': natural_query,
            'sql_query': sql_query,
            'validation': validation,
            'row_count': len(result_df)
        })

        return validation

    def _validate_semantic_meaning(
        self,
        natural_query: str,
        sql_query: str,
        result_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Validate that results match semantic intent of query"""

        check = {
            'confidence': 1.0,
            'warnings': [],
            'matches_intent': True
        }

        nl_lower = natural_query.lower()
        sql_lower = sql_query.lower()

        # Check aggregation expectations
        if any(word in nl_lower for word in ['total', 'sum', 'all']):
            if 'sum(' not in sql_lower:
                check['warnings'].append(
                    "Query asked for 'total' but SQL doesn't use SUM()"
                )
                check['confidence'] *= 0.8

        if any(word in nl_lower for word in ['average', 'avg', 'mean']):
            if 'avg(' not in sql_lower:
                check['warnings'].append(
                    "Query asked for 'average' but SQL doesn't use AVG()"
                )
                check['confidence'] *= 0.8

        if any(word in nl_lower for word in ['count', 'how many', 'number of']):
            if 'count(' not in sql_lower and len(result_df) > 10:
                check['warnings'].append(
                    "Query asked for count but returned many rows - verify correctness"
                )
                check['confidence'] *= 0.9

        # Check filtering expectations
        if 'where' in nl_lower or 'in' in nl_lower or 'from' in nl_lower:
            if 'where' not in sql_lower:
                check['warnings'].append(
                    "Query implied filtering but SQL has no WHERE clause"
                )
                check['confidence'] *= 0.85

        # Check TOP/LIMIT expectations
        if any(word in nl_lower for word in ['top', 'best', 'highest', 'lowest']):
            if 'limit' not in sql_lower and 'top' not in sql_lower:
                check['warnings'].append(
                    "Query asked for 'top' results but SQL has no LIMIT"
                )
                check['confidence'] *= 0.9

        # Check grouping expectations
        if any(word in nl_lower for word in ['by product', 'by region', 'breakdown', 'each']):
            if 'group by' not in sql_lower:
                check['warnings'].append(
                    "Query implied grouping but SQL has no GROUP BY"
                )
                check['confidence'] *= 0.85

        return check

    def _check_data_quality(self, result_df: pd.DataFrame) -> Dict[str, Any]:
        """Check data quality of results"""

        quality = {
            'has_nulls': False,
            'null_columns': [],
            'row_count': len(result_df),
            'column_count': len(result_df.columns) if not result_df.empty else 0,
            'issues': []
        }

        if not result_df.empty:
            # Check for NULL values
            null_cols = result_df.columns[result_df.isnull().any()].tolist()
            if null_cols:
                quality['has_nulls'] = True
                quality['null_columns'] = null_cols
                quality['issues'].append(f"NULL values found in: {', '.join(null_cols)}")

            # Check for duplicate rows
            duplicates = result_df.duplicated().sum()
            if duplicates > 0:
                quality['issues'].append(f"Found {duplicates} duplicate rows")

        return quality

    def _validate_sql_structure(
        self,
        sql_query: str,
        natural_query: str
    ) -> Dict[str, Any]:
        """Validate SQL query structure"""

        check = {
            'warnings': [],
            'suggestions': []
        }

        sql_lower = sql_query.lower()

        # Check for SELECT *
        if 'select *' in sql_lower:
            check['suggestions'].append(
                "Consider selecting specific columns instead of SELECT *"
            )

        # Check for dangerous operations
        if any(op in sql_lower for op in ['delete', 'drop', 'truncate', 'update']):
            check['warnings'].append(
                "⚠️ Query contains potentially dangerous operations"
            )

        # Check for ORDER BY with aggregations
        if 'group by' in sql_lower and 'order by' not in sql_lower:
            check['suggestions'].append(
                "Consider adding ORDER BY to sort grouped results"
            )

        return check

    def get_validation_summary(self) -> str:
        """Get summary of recent validations"""

        if not self.validation_history:
            return "No validation history available"

        recent = self.validation_history[-10:]  # Last 10

        total = len(recent)
        valid = sum(1 for v in recent if v['validation']['is_valid'])
        avg_confidence = sum(v['validation']['confidence'] for v in recent) / total

        summary = f"""
Validation Summary (Last {total} queries):
  ✓ Valid Queries: {valid}/{total} ({valid/total*100:.1f}%)
  📊 Average Confidence: {avg_confidence:.1%}
  ⚠️ Queries with Warnings: {sum(1 for v in recent if v['validation']['warnings'])}
        """

        return summary.strip()

