#user_services.py
import sqlite3
import os

class UserService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'nutrition.db')
        print(f"Database file path: {self.db_path}")

    def register_user(self, phone_number):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute("SELECT 1 FROM authorized_users WHERE phone_number = ?", (phone_number,))

            if cursor.fetchone() is None:
                # User doesn't exist, insert new user
                cursor.execute("INSERT INTO authorized_users (phone_number) VALUES (?)", (phone_number,))
                conn.commit()
                print(f"New user registered: {phone_number}")
            else:
                print(f"User already registered: {phone_number}")

            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def set_user_goals(self, phone_number, calories, protein, carbs, fat):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Insert or update user goals
            cursor.execute("""
                INSERT INTO user_goals (phone_number, calories, protein, carbs, fat)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(phone_number) 
                DO UPDATE SET 
                    calories = excluded.calories,
                    protein = excluded.protein,
                    carbs = excluded.carbs,
                    fat = excluded.fat
            """, (phone_number, calories, protein, carbs, fat))
            conn.commit()
            print(
                f"Goals updated for user: {phone_number} - Calories: {calories}, Protein: {protein}, Carbs: {carbs}, Fat: {fat}")
            return True

        except sqlite3.Error as e:
            print(f"Database error in set_user_goals: {e}")
            return False

        finally:
            if conn:
                conn.close()

    def get_user_goals(self, phone_number):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT calories, protein, carbs, fat 
                FROM user_goals
                WHERE phone_number = ?
            """, (phone_number,))
            result = cursor.fetchone()

            if result:
                return {
                    "calories": result[0],
                    "protein": result[1],
                    "carbs": result[2],
                    "fat": result[3]
                }
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()