import sqlite3
import json
from datetime import date, datetime
import os


def test_database_connection(db_path):
    """Test if we can connect to the database and print basic info"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("\n=== Database Connection Test ===")
        print(f"Successfully connected to database at: {db_path}")
        print("\nAvailable tables:")
        for table in tables:
            print(f"- {table[0]}")
            # Get count of records in each table
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  Records: {count}")

        return True
    except sqlite3.Error as e:
        print(f"\n❌ Database connection error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def query_database(db_path):
    """Enhanced database query tool with additional functionality"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        while True:
            print("\n=== Database Query Tool ===")
            print("1. View all authorized users")
            print("2. View all user goals")
            print("3. View today's meals")
            print("4. View all meals")
            print("5. View daily tracking")
            print("6. Run connection test")
            print("7. Exit")

            choice = input("\nEnter your choice (1-7): ")

            if choice == '1':
                cursor.execute("SELECT * FROM authorized_users")
                users = cursor.fetchall()
                print("\nAuthorized Users:")
                for user in users:
                    print(f"Phone Number: {user[0]}")

            elif choice == '2':
                cursor.execute("SELECT * FROM user_goals")
                goals = cursor.fetchall()
                print("\nUser Goals:")
                for goal in goals:
                    print(f"\nPhone Number: {goal[0]}")
                    print(f"Calories: {goal[1]}")
                    print(f"Protein: {goal[2]}g")
                    print(f"Carbs: {goal[3]}g")
                    print(f"Fat: {goal[4]}g")

            elif choice == '3':
                cursor.execute("""
                    SELECT * FROM meals 
                    WHERE date = date('now')
                    ORDER BY meal_time
                """)
                meals = cursor.fetchall()
                print("\nToday's Meals:")
                for meal in meals:
                    print(f"\nTime: {meal[3]}")
                    print(f"Food Items: {meal[4]}")
                    print(f"Calories: {meal[5]}")
                    print(f"Protein: {meal[6]}g")
                    print(f"Carbs: {meal[7]}g")
                    print(f"Fat: {meal[8]}g")

            elif choice == '4':
                cursor.execute("SELECT * FROM meals ORDER BY date, meal_time")
                meals = cursor.fetchall()
                print("\nAll Meals:")
                for meal in meals:
                    print(f"\nDate: {meal[2]}")
                    print(f"Time: {meal[3]}")
                    print(f"Food Items: {meal[4]}")
                    print(f"Calories: {meal[5]}")
                    print(f"Protein: {meal[6]}g")
                    print(f"Carbs: {meal[7]}g")
                    print(f"Fat: {meal[8]}g")

            elif choice == '5':
                cursor.execute("SELECT * FROM daily_tracking ORDER BY date")
                tracking = cursor.fetchall()
                print("\nDaily Tracking:")
                for record in tracking:
                    print(f"\nDate: {record[2]}")
                    print(f"Phone Number: {record[1]}")
                    print(f"Total Calories: {record[3]}")
                    print(f"Total Protein: {record[4]}g")
                    print(f"Total Carbs: {record[5]}g")
                    print(f"Total Fat: {record[6]}g")

            elif choice == '6':
                test_database_connection(db_path)

            elif choice == '7':
                print("\nExiting query tool...")
                break

            else:
                print("\n❌ Invalid choice. Please try again.")

            input("\nPress Enter to continue...")

    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    # Try to find the database file
    possible_paths = [
        '/Users/tfg/food-tracker-bot/src/database/database/nutrition.db',
        os.path.join(os.path.dirname(__file__), 'database', 'database', 'nutrition.db'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'nutrition.db')
    ]

    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

    if db_path is None:
        print("❌ Could not find the database file. Please enter the correct path:")
        db_path = input("Database path: ")
        if not os.path.exists(db_path):
            print("❌ Invalid database path. Exiting...")
            exit(1)

    # First test the connection
    if test_database_connection(db_path):
        # If connection successful, run the query tool
        query_database(db_path)
    else:
        print("❌ Unable to proceed due to database connection error.")