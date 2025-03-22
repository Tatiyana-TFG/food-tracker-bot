import os
import psycopg2
import sqlite3


class UserService:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.use_sqlite = not self.db_url
        if self.use_sqlite:
            self.db_path = 'nutrition.db'
            print(f"UserService initialized with SQLite: {self.db_path}")
        else:
            print(f"UserService initialized with PostgreSQL: {self.db_url}")

    def _get_connection(self):
        """Get database connection based on environment"""
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Enable foreign keys
            conn.execute('PRAGMA foreign_keys = ON')
            return conn
        else:
            return psycopg2.connect(self.db_url)

    def register_user(self, phone_number):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if user already exists
            if self.use_sqlite:
                cursor.execute("SELECT 1 FROM authorized_users WHERE phone_number = ?", (phone_number,))
            else:
                cursor.execute("SELECT 1 FROM authorized_users WHERE phone_number = %s", (phone_number,))

            if cursor.fetchone() is None:
                # User doesn't exist, insert new user
                if self.use_sqlite:
                    cursor.execute("INSERT INTO authorized_users (phone_number) VALUES (?)", (phone_number,))
                else:
                    cursor.execute("INSERT INTO authorized_users (phone_number) VALUES (%s)", (phone_number,))
                conn.commit()
                print(f"New user registered: {phone_number}")
            else:
                print(f"User already registered: {phone_number}")

            return True
        except Exception as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def set_user_goals(self, phone_number, calories, protein, carbs, fat):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Insert or update user goals
            if self.use_sqlite:
                # Check if goals exist for this user
                cursor.execute(
                    "SELECT 1 FROM user_goals WHERE phone_number = ?",
                    (phone_number,)
                )

                if cursor.fetchone():
                    # Update existing goals
                    cursor.execute("""
                        UPDATE user_goals 
                        SET calories = ?, protein = ?, carbs = ?, fat = ?
                        WHERE phone_number = ?
                    """, (calories, protein, carbs, fat, phone_number))
                else:
                    # Insert new goals
                    cursor.execute("""
                        INSERT INTO user_goals (phone_number, calories, protein, carbs, fat)
                        VALUES (?, ?, ?, ?, ?)
                    """, (phone_number, calories, protein, carbs, fat))
            else:
                # PostgreSQL version with ON CONFLICT
                cursor.execute("""
                    INSERT INTO user_goals (phone_number, calories, protein, carbs, fat)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (phone_number)
                    DO UPDATE SET
                        calories = EXCLUDED.calories,
                        protein = EXCLUDED.protein,
                        carbs = EXCLUDED.carbs,
                        fat = EXCLUDED.fat
                """, (phone_number, calories, protein, carbs, fat))

            conn.commit()
            print(
                f"Goals updated for user: {phone_number} - Calories: {calories}, Protein: {protein}, Carbs: {carbs}, Fat: {fat}")
            return True

        except Exception as e:
            print(f"Database error in set_user_goals: {e}")
            if conn:
                conn.rollback()
            return False

        finally:
            if conn:
                conn.close()

    def get_user_goals(self, phone_number):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if self.use_sqlite:
                cursor.execute("""
                    SELECT calories, protein, carbs, fat
                    FROM user_goals
                    WHERE phone_number = ?
                """, (phone_number,))
            else:
                cursor.execute("""
                    SELECT calories, protein, carbs, fat
                    FROM user_goals
                    WHERE phone_number = %s
                """, (phone_number,))

            result = cursor.fetchone()

            if result:
                if self.use_sqlite:
                    # Convert to dict if using SQLite with row_factory
                    return {
                        "calories": result['calories'],
                        "protein": result['protein'],
                        "carbs": result['carbs'],
                        "fat": result['fat']
                    }
                else:
                    # For PostgreSQL
                    return {
                        "calories": result[0],
                        "protein": result[1],
                        "carbs": result[2],
                        "fat": result[3]
                    }
            else:
                return None
        except Exception as e:
            print(f"Database error in get_user_goals: {e}")
            return None
        finally:
            if conn:
                conn.close()