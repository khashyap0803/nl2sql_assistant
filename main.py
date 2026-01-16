import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import config
from src.utils.logger import logger

REMOTE_SERVER_URL = None


def test_database():
    logger.section("NL2SQL Voice Assistant - Database Test")

    logger.i("TEST", "Starting database connection test")
    db = DatabaseController()

    if db.connect():
        logger.i("TEST", "Database connection successful")

        tables = db.get_table_names()
        logger.d("TEST", f"Tables found: {tables}")

        if 'sales' in tables:
            result = db.execute_query("SELECT * FROM sales LIMIT 5")
            print("\n[DATA] Sample data from sales table:")
            print(result)

            stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(amount) as total_sales,
                    AVG(amount) as avg_sale
                FROM sales
            """)
            print("\n[STATS] Database Statistics:")
            print(stats)

            db.close()
            logger.i("TEST", "Database test completed successfully")
            return True
        else:
            logger.w("TEST", "'sales' table not found")
            print("\n[WARNING] 'sales' table not found!")
            print("   Please run the following steps:")
            print("   1. Open pgAdmin")
            print("   2. Create database 'nl2sql_db' if it doesn't exist")
            print("   3. Run the SQL in 'src/database/schema.sql'")
            print("   4. Or run: python src/database/populate_db.py")
            db.close()
            return False
    else:
        logger.e("TEST", "Could not connect to database")
        print("\n[ERROR] Could not connect to database")
        print("\n[HELP] Troubleshooting:")
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
    global REMOTE_SERVER_URL
    
    logger.separator("=", 80)
    logger.i("MAIN", "NL2SQL Voice Assistant Starting...")
    logger.separator("=", 80)

    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            from src.database.db_controller import DatabaseController
            success = test_database()
            print("\n" + "=" * 60)
            if success:
                print("  [OK] All tests passed! Ready to launch GUI")
                print("  Run: python main.py")
                logger.i("MAIN", "Tests passed - application ready")
            else:
                print("  [WARNING] Please fix database connection first")
                logger.w("MAIN", "Tests failed - database connection issues")
            print("=" * 60)
            return
            
        elif sys.argv[1] == '--server' and len(sys.argv) > 2:
            REMOTE_SERVER_URL = sys.argv[2]
            logger.i("MAIN", f"Remote mode: connecting to {REMOTE_SERVER_URL}")
            print(f"[REMOTE MODE] Connecting to server: {REMOTE_SERVER_URL}")
            print()
            
            from src.remote.client import RemoteNL2SQLClient
            client = RemoteNL2SQLClient(REMOTE_SERVER_URL)
            
            if not client.enabled:
                print("\n[ERROR] Cannot connect to remote server!")
                print("  Make sure the server is running and the URL is correct.")
                print(f"  URL: {REMOTE_SERVER_URL}")
                return
            
            print("\n[OK] Connected to remote server!")
            print("Launching remote GUI...\n")
            
            from src.gui.main_window import main as gui_main
            gui_main(remote_server_url=REMOTE_SERVER_URL)
            return
            
        elif sys.argv[1] == '--help':
            print("NL2SQL Voice Assistant")
            print("\nUsage:")
            print("  python main.py                      # Launch GUI (local mode)")
            print("  python main.py --server <url>       # Launch GUI (remote mode)")
            print("  python main.py --test               # Test database connection")
            print("  python main.py --help               # Show this help message")
            print("\nRemote Mode:")
            print("  Connect to a remote NL2SQL server for GPU processing")
            print("  Example: python main.py --server https://abc123.trycloudflare.com")
            print("\nLog files are saved in: logs/")
            return

    print("Launching NL2SQL Voice Assistant GUI (Local Mode)...")
    print("(Use --server <url> for remote mode, --help for more options)\n")
    logger.i("MAIN", "Launching GUI application (local mode)")

    from src.database.db_controller import DatabaseController
    db = DatabaseController()
    if not db.connect():
        logger.e("MAIN", "Database connection failed at startup")
        print("\n[WARNING] Could not connect to database!")
        print("The application will launch, but queries will fail.")
        print("Please check your database configuration.\n")
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    else:
        logger.i("MAIN", "Database connection verified at startup")
        print("[OK] Database connection OK")
        db.close()

    logger.i("MAIN", "Starting GUI main loop")
    from src.gui.main_window import main as gui_main
    gui_main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.i("MAIN", "Application interrupted by user (Ctrl+C)")
        print("\n\nApplication terminated by user")
    except Exception as e:
        logger.e("MAIN", f"Unexpected error in main: {str(e)}", e)
        print(f"\n[ERROR] Unexpected error: {e}")
        print(f"Check log file in logs/ for details")
    finally:
        logger.separator("=", 80)
        logger.i("MAIN", "Application shutdown complete")
        logger.separator("=", 80)

