import psycopg2
import json
from datetime import date, datetime
import os

class NutritionService:
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        print(f"NutritionService initialized with db_url: {self.db_url}")

    def log_meal(self, phone_number, meal_data):
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_date = date.today().isoformat()

            # Insert meal data
            cursor.execute("""
                INSERT INTO meals (
                    phone_number, date, meal_time, food_items, 
                    calories, protein, carbs, fat, analysis_text
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                phone_number,
                current_date,
                current_time,
                json.dumps(meal_data.get('food_items', []), ensure_ascii=False),
                meal_data.get('calories', 0),
                meal_data.get('protein', 0),
                meal_data.get('carbs', 0),
                meal_data.get('fat', 0),
                meal_data.get('analysis_text', '')
            ))

            # Update daily tracking to sum ALL meals for the day
            cursor.execute("""
                DELETE FROM daily_tracking 
                WHERE phone_number = %s AND date = %s
            """, (phone_number, current_date))

            cursor.execute("""
                INSERT INTO daily_tracking 
                (phone_number, date, total_calories, total_protein, total_carbs, total_fat)
                SELECT 
                    %s, 
                    %s, 
                    SUM(calories),
                    SUM(protein),
                    SUM(carbs),
                    SUM(fat)
                FROM meals 
                WHERE phone_number = %s AND date = %s
            """, (phone_number, current_date, phone_number, current_date))

            conn.commit()
            return True

        except Exception as e:
            print(f"Error logging meal: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()

    def get_daily_progress(self, phone_number):
        try:
            print(f"\n=== Debug: Getting daily progress for {phone_number} ===")
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Check what meals exist in the database
            print("\nChecking all meals in database:")
            cursor.execute("SELECT date, calories, protein, carbs, fat FROM meals")
            all_meals = cursor.fetchall()
            print(f"All meals: {all_meals}")

            today = date.today().isoformat()
            print(f"\nToday's date (ISO format): {today}")

            # Check today's meals
            cursor.execute("""
                SELECT date, calories, protein, carbs, fat 
                FROM meals 
                WHERE phone_number = %s AND date = %s
            """, (phone_number, today))
            todays_meals = cursor.fetchall()
            print(f"\nToday's meals: {todays_meals}")

            # Progress query with totals
            progress_query = """
            SELECT 
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(carbs), 0) as total_carbs,
                COALESCE(SUM(fat), 0) as total_fat
            FROM meals
            WHERE phone_number = %s AND date = %s
            """

            cursor.execute(progress_query, (phone_number, today))
            result = cursor.fetchone()
            print(f"\nProgress query result: {result}")

            totals = {
                "totals": {
                    "calories": float(result[0]) if result[0] else 0,
                    "protein": float(result[1]) if result[1] else 0,
                    "carbs": float(result[2]) if result[2] else 0,
                    "fat": float(result[3]) if result[3] else 0
                }
            }

            print(f"Returning totals: {totals}")
            return totals

        except psycopg2.Error as e:
            print(f"Database error in get_daily_progress: {e}")
            return None
        finally:
            if conn:
                conn.close()