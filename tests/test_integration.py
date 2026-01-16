import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.db_controller import DatabaseController
from src.llm.nl2sql_converter import NL2SQLConverter
from src.reports.report_generator import ReportGenerator
import pandas as pd


class TestDatabaseController:

    def test_connection(self):
        db = DatabaseController()
        assert db.connect() == True
        db.close()

    def test_simple_query(self):
        db = DatabaseController()
        db.connect()
        result = db.execute_query("SELECT COUNT(*) FROM sales")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        db.close()

    def test_invalid_query(self):
        db = DatabaseController()
        db.connect()
        result = db.execute_query("SELECT * FROM nonexistent_table")
        assert isinstance(result, str)
        assert "Error" in result
        db.close()


class TestNL2SQLConverter:

    def test_total_sales(self):
        converter = NL2SQLConverter()
        sql = converter.convert("total sales")
        assert "SELECT" in sql.upper()
        assert "SUM" in sql.upper()
        assert "sales" in sql.lower()

    def test_sales_by_product(self):
        converter = NL2SQLConverter()
        sql = converter.convert("sales by product")
        assert "GROUP BY" in sql.upper()
        assert "product" in sql.lower()

    def test_top_n(self):
        converter = NL2SQLConverter()
        sql = converter.convert("top 5 products")
        assert "LIMIT 5" in sql.upper()


class TestReportGenerator:

    def test_chart_creation(self):
        df = pd.DataFrame({
            'Product': ['Widget', 'Gadget'],
            'Sales': [1000, 2000]
        })
        rg = ReportGenerator()
        fig = rg.create_chart(df)
        assert fig is not None

    def test_csv_export(self):
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        rg = ReportGenerator()
        success = rg.export_to_csv(df, 'test_output.csv')
        assert success == True

        if os.path.exists('test_output.csv'):
            os.remove('test_output.csv')


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
