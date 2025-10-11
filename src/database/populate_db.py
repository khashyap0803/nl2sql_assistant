"""
Database Population Script
Populates the sales database with realistic sample data (50+ records)
"""

import psycopg2
import random
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import config

def populate_database():
    """Populate database with 50+ sample sales records"""

    print("=" * 60)
    print("DATABASE POPULATION SCRIPT")
    print("=" * 60)

    # Database configuration
    db_config = {
        'dbname': config.get('database', 'dbname'),
        'user': config.get('database', 'user'),
        'password': config.get('database', 'password'),
        'host': config.get('database', 'host'),
        'port': config.get('database', 'port')
    }

    try:
        # Connect to database
        print(f"\n✓ Connecting to {db_config['dbname']}@{db_config['host']}...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        # Clear existing data
        print("✓ Clearing existing data...")
        cur.execute("DELETE FROM sales")
        conn.commit()

        # Sample data arrays
        products = [
            'Laptop', 'Desktop', 'Monitor', 'Keyboard', 'Mouse',
            'Headphones', 'Webcam', 'Printer', 'Scanner', 'Tablet',
            'Smartphone', 'Smartwatch', 'Speaker', 'Router', 'Cable'
        ]

        regions = ['North', 'South', 'East', 'West']

        # Generate 50+ sales records
        print("✓ Generating 50+ sales records...")
        sales_data = []

        # Start date: 6 months ago
        start_date = datetime.now() - timedelta(days=180)

        for i in range(60):  # Generate 60 records
            # Random date within last 6 months
            days_offset = random.randint(0, 180)
            sale_date = start_date + timedelta(days=days_offset)

            # Random product and region
            product = random.choice(products)
            region = random.choice(regions)

            # Amount based on product type (realistic pricing)
            amount_ranges = {
                'Laptop': (800, 2500),
                'Desktop': (600, 2000),
                'Monitor': (150, 600),
                'Keyboard': (20, 150),
                'Mouse': (10, 100),
                'Headphones': (30, 300),
                'Webcam': (40, 200),
                'Printer': (100, 500),
                'Scanner': (80, 400),
                'Tablet': (200, 1000),
                'Smartphone': (300, 1500),
                'Smartwatch': (150, 600),
                'Speaker': (50, 400),
                'Router': (40, 250),
                'Cable': (5, 50)
            }

            min_amount, max_amount = amount_ranges.get(product, (50, 500))
            amount = round(random.uniform(min_amount, max_amount), 2)

            sales_data.append((sale_date, product, region, amount))

        # Insert data
        print(f"✓ Inserting {len(sales_data)} records...")
        insert_query = """
            INSERT INTO sales (date, product, region, amount)
            VALUES (%s, %s, %s, %s)
        """
        cur.executemany(insert_query, sales_data)
        conn.commit()

        # Verify insertion
        cur.execute("SELECT COUNT(*) FROM sales")
        count = cur.fetchone()[0]
        print(f"\n✅ SUCCESS: Inserted {count} sales records")

        # Show statistics
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)

        # Total sales
        cur.execute("SELECT SUM(amount) as total_sales FROM sales")
        total = cur.fetchone()[0]
        print(f"Total Sales: ${total:,.2f}")

        # Average sale
        cur.execute("SELECT AVG(amount) as avg_sale FROM sales")
        avg = cur.fetchone()[0]
        print(f"Average Sale: ${avg:,.2f}")

        # Sales by region
        print("\nSales by Region:")
        cur.execute("""
            SELECT region, COUNT(*) as count, SUM(amount) as total
            FROM sales
            GROUP BY region
            ORDER BY total DESC
        """)
        for region, count, total in cur.fetchall():
            print(f"  {region:10} - {count:2} sales - ${total:,.2f}")

        # Top 5 products
        print("\nTop 5 Products by Revenue:")
        cur.execute("""
            SELECT product, COUNT(*) as count, SUM(amount) as total
            FROM sales
            GROUP BY product
            ORDER BY total DESC
            LIMIT 5
        """)
        for i, (product, count, total) in enumerate(cur.fetchall(), 1):
            print(f"  {i}. {product:15} - {count:2} sales - ${total:,.2f}")

        # Date range
        cur.execute("SELECT MIN(date), MAX(date) FROM sales")
        min_date, max_date = cur.fetchone()
        print(f"\nDate Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

        print("\n" + "=" * 60)
        print("✅ Database population complete!")
        print("=" * 60)

        # Close connection
        cur.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    success = populate_database()

    if success:
        print("\n✓ You can now run the application with more test data")
        print("  Run: python main.py")
    else:
        print("\n⚠️  Please check your database configuration")

    print("\n")
