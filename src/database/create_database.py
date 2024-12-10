import sqlite3
import os

def initialize_database():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database', 'nutrition.db')
    print(f"Database file path: {db_path}")

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create authorized_users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorized_users (
                phone_number TEXT PRIMARY KEY
            )
        """)

        # Create user_goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_goals (
                phone_number TEXT PRIMARY KEY,
                calories INTEGER,
                protein INTEGER,
                carbs INTEGER,
                fat INTEGER,
                FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
            )
        """)

        # Create meals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                date TEXT,
                meal_time TEXT,
                food_items TEXT,
                calories REAL,
                protein REAL,
                carbs REAL,
                fat REAL,
                analysis_text TEXT,
                FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
            )
        """)

        # Create daily_tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                date TEXT,
                total_calories REAL,
                total_protein REAL,
                total_carbs REAL,
                total_fat REAL,
                FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
            )
        """)

        # Commit changes and close the connection
        conn.commit()
        print(f"Database created successfully at {db_path}")
    except sqlite3.Error as e:
        print(f"Error while creating tables: {e}")
    finally:
        conn.close()

# Run the function to create the database and tables
if __name__ == "__main__":
    initialize_database()