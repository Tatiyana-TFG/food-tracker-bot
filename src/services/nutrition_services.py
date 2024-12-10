#nutrition_services.py
import sqlite3
import json
from datetime import date, datetime
import sys
from pathlib import Path
import os

class NutritionService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'nutrition.db')
        print(f"NutritionService initialized with db_path: {self.db_path}")

    def log_meal(self, phone_number, meal_data):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_date = date.today().isoformat()

            # Insert meal data (this part is fine)
            cursor.execute("""
                INSERT INTO meals (
                    phone_number, date, meal_time, food_items, 
                    calories, protein, carbs, fat, analysis_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            # FIXED: Update daily tracking to properly sum ALL meals for the day
            cursor.execute("""
                DELETE FROM daily_tracking 
                WHERE phone_number = ? AND date = ?
            """, (phone_number, current_date))

            cursor.execute("""
                INSERT INTO daily_tracking 
                (phone_number, date, total_calories, total_protein, total_carbs, total_fat)
                SELECT 
                    ?, 
                    ?, 
                    SUM(calories),
                    SUM(protein),
                    SUM(carbs),
                    SUM(fat)
                FROM meals 
                WHERE phone_number = ? AND date = ?
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # First, let's check what meals exist in the database
            print("\nChecking all meals in database:")
            cursor.execute("SELECT date, calories, protein, carbs, fat FROM meals")
            all_meals = cursor.fetchall()
            print(f"All meals: {all_meals}")

            # Now check today's date format
            today = date.today().isoformat()
            print(f"\nToday's date (ISO format): {today}")

            # Check specifically for today's meals
            cursor.execute("""
                SELECT date, calories, protein, carbs, fat 
                FROM meals 
                WHERE phone_number = ? AND date = ?
            """, (phone_number, today))
            todays_meals = cursor.fetchall()
            print(f"\nToday's meals: {todays_meals}")

            # Original progress query with totals
            progress_query = """
            SELECT 
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(carbs), 0) as total_carbs,
                COALESCE(SUM(fat), 0) as total_fat
            FROM meals
            WHERE phone_number = ? AND date = ?
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

        except sqlite3.Error as e:
            print(f"Database error in get_daily_progress: {e}")
            return None
        finally:
            if conn:
                conn.close()