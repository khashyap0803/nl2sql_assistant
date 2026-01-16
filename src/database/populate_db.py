import psycopg2
import random
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import config

def populate_database():
    print("=" * 60)
    print("DATABASE POPULATION SCRIPT")
    print("=" * 60)

    db_config = {
        'dbname': config.get('database', 'dbname'),
        'user': config.get('database', 'user'),
        'password': config.get('database', 'password'),
        'host': config.get('database', 'host'),
        'port': config.get('database', 'port')
    }

    try:
        print(f"\nConnecting to {db_config['dbname']}@{db_config['host']}...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        print("Clearing existing data...")
        cur.execute("DELETE FROM sales")
        conn.commit()

        products = [
            'Laptop', 'Desktop', 'Monitor', 'Keyboard', 'Mouse',
            'Headphones', 'Webcam', 'Printer', 'Scanner', 'Tablet',
            'Smartphone', 'Smartwatch', 'Speaker', 'Router', 'Cable'
        ]

        regions = ['North', 'South', 'East', 'West']

        print("Generating 50+ sales records...")
        sales_data = []

        start_date = datetime.now() - timedelta(days=180)

        for i in range(60):
            days_offset = random.randint(0, 180)
            sale_date = start_date + timedelta(days=days_offset)

            product = random.choice(products)
            region = random.choice(regions)

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

        print(f"Inserting {len(sales_data)} records...")
        insert_query = """
            INSERT INTO sales (date, product, region, amount)
            VALUES (%s, %s, %s, %s)
        """
        cur.executemany(insert_query, sales_data)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM sales")
        count = cur.fetchone()[0]
        print(f"\nSUCCESS: Inserted {count} sales records")

        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)

        cur.execute("SELECT SUM(amount) as total_sales FROM sales")
        total = cur.fetchone()[0]
        print(f"Total Sales: Rs {total:,.2f}")

        cur.execute("SELECT AVG(amount) as avg_sale FROM sales")
        avg = cur.fetchone()[0]
        print(f"Average Sale: Rs {avg:,.2f}")

        print("\nSales by Region:")
        cur.execute("""
            SELECT region, COUNT(*) as count, SUM(amount) as total
            FROM sales
            GROUP BY region
            ORDER BY total DESC
        """)
        for region, count, total in cur.fetchall():
            print(f"  {region:10} - {count:2} sales - Rs {total:,.2f}")

        print("\nTop 5 Products by Revenue:")
        cur.execute("""
            SELECT product, COUNT(*) as count, SUM(amount) as total
            FROM sales
            GROUP BY product
            ORDER BY total DESC
            LIMIT 5
        """)
        for i, (product, count, total) in enumerate(cur.fetchall(), 1):
            print(f"  {i}. {product:15} - {count:2} sales - Rs {total:,.2f}")

        cur.execute("SELECT MIN(date), MAX(date) FROM sales")
        min_date, max_date = cur.fetchone()
        print(f"\nDate Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

        print("\n" + "=" * 60)
        print("Database population complete!")
        print("=" * 60)

        cur.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    success = populate_database()

    if success:
        print("\nYou can now run the application with more test data")
        print("  Run: python main.py")
    else:
        print("\nPlease check your database configuration")

    print("\n")
