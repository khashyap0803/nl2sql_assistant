"""
NL2SQL Voice Assistant - Main Entry Point
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from src.database.db_controller import DatabaseController
from src.gui.main_window import main as gui_main
from config import config
from src.utils.logger import logger


def test_database():
    """Test database connection and show sample data"""
    logger.section("NL2SQL Voice Assistant - Database Test")

    logger.i("TEST", "Starting database connection test")
    db = DatabaseController()

    if db.connect():
        logger.i("TEST", "Database connection successful")

        # Check if sales table exists
        tables = db.get_table_names()
        logger.d("TEST", f"Tables found: {tables}")

        if 'sales' in tables:
            # Show sample data
            result = db.execute_query("SELECT * FROM sales LIMIT 5")
            print("\n📊 Sample data from sales table:")
            print(result)

            # Show statistics
            stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(amount) as total_sales,
                    AVG(amount) as avg_sale
                FROM sales
            """)
            print("\n📈 Database Statistics:")
            print(stats)

            db.close()
            logger.i("TEST", "Database test completed successfully")
            return True
        else:
            logger.w("TEST", "'sales' table not found")
            print("\n⚠️  'sales' table not found!")
            print("   Please run the following steps:")
            print("   1. Open pgAdmin")
            print("   2. Create database 'nl2sql_db' if it doesn't exist")
            print("   3. Run the SQL in 'src/database/schema.sql'")
            print("   4. Or run: python src/database/populate_db.py")
            db.close()
            return False
    else:
        logger.e("TEST", "Could not connect to database")
        print("\n❌ Could not connect to database")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check credentials in config.py")
        print("   3. Verify database 'nl2sql_db' exists")
        print(f"\n   Current settings:")
        print(f"   - Database: {config.get('database', 'dbname')}")
        print(f"   - User: {config.get('database', 'user')}")
        print(f"   - Host: {config.get('database', 'host')}")
        print(f"   - Port: {config.get('database', 'port')}")
        return False


def main():
    """Main application entry point"""

    logger.separator("=", 80)
    logger.i("MAIN", "NL2SQL Voice Assistant Starting...")
    logger.separator("=", 80)

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            # Run database test
            success = test_database()
            print("\n" + "=" * 60)
            if success:
                print("  ✓ All tests passed! Ready to launch GUI")
                print("  Run: python main.py")
                logger.i("MAIN", "Tests passed - application ready")
            else:
                print("  ⚠️  Please fix database connection first")
                logger.w("MAIN", "Tests failed - database connection issues")
            print("=" * 60)
            return
        elif sys.argv[1] == '--help':
            print("NL2SQL Voice Assistant")
            print("\nUsage:")
            print("  python main.py          # Launch GUI application")
            print("  python main.py --test   # Test database connection")
            print("  python main.py --help   # Show this help message")
            print("\nLog files are saved in: logs/")
            print("View logs in real-time with the Log Viewer (Menu > View Logs)")
            return

    # Default: Launch GUI
    print("Launching NL2SQL Voice Assistant GUI...")
    print("(Use --test to run database tests, --help for more options)\n")
    logger.i("MAIN", "Launching GUI application")

    # Test database connection first
    db = DatabaseController()
    if not db.connect():
        logger.e("MAIN", "Database connection failed at startup")
        print("\n⚠️  WARNING: Could not connect to database!")
        print("The application will launch, but queries will fail.")
        print("Please check your database configuration.\n")
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    else:
        logger.i("MAIN", "Database connection verified at startup")
        print("✓ Database connection OK")
        db.close()

    # Launch GUI
    logger.i("MAIN", "Starting GUI main loop")
    gui_main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.i("MAIN", "Application interrupted by user (Ctrl+C)")
        print("\n\nApplication terminated by user")
    except Exception as e:
        logger.e("MAIN", f"Unexpected error in main: {str(e)}", e)
        print(f"\n❌ Unexpected error: {e}")
        print(f"Check log file in logs/ for details")
    finally:
        logger.separator("=", 80)
        logger.i("MAIN", "Application shutdown complete")
        logger.separator("=", 80)
