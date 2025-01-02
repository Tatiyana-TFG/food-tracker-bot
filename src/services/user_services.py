import psycopg2
import os

class UserService:
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        print(f"UserService initialized with db_url: {self.db_url}")

    def register_user(self, phone_number):
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute("SELECT 1 FROM authorized_users WHERE phone_number = %s", (phone_number,))

            if cursor.fetchone() is None:
                # User doesn't exist, insert new user
                cursor.execute("INSERT INTO authorized_users (phone_number) VALUES (%s)", (phone_number,))
                conn.commit()
                print(f"New user registered: {phone_number}")
            else:
                print(f"User already registered: {phone_number}")

            return True
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def set_user_goals(self, phone_number, calories, protein, carbs, fat):
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Insert or update user goals
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

        except psycopg2.Error as e:
            print(f"Database error in set_user_goals: {e}")
            return False

        finally:
            if conn:
                conn.close()

    def get_user_goals(self, phone_number):
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT calories, protein, carbs, fat
                FROM user_goals
                WHERE phone_number = %s
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
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()