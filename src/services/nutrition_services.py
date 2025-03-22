import os
import json
from datetime import date, datetime
import psycopg2
import sqlite3


class NutritionService:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.use_sqlite = not self.db_url
        if self.use_sqlite:
            self.db_path = 'nutrition.db'
            print(f"NutritionService initialized with SQLite: {self.db_path}")
        else:
            print(f"NutritionService initialized with PostgreSQL: {self.db_url}")

    def _get_connection(self):
        """Get database connection based on environment"""
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This makes rows accessible by column name
            # Enable foreign keys
            conn.execute('PRAGMA foreign_keys = ON')
            return conn
        else:
            return psycopg2.connect(self.db_url)

    def log_meal(self, phone_number, meal_data):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_date = date.today().isoformat()

            # Insert meal data
            if self.use_sqlite:
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

                # Update daily tracking - first delete existing
                cursor.execute("""
                    DELETE FROM daily_tracking 
                    WHERE phone_number = ? AND date = ?
                """, (phone_number, current_date))

                # Calculate new totals from all meals
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
            else:
                # PostgreSQL version
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
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_daily_progress(self, phone_number):
        conn = None
        try:
            print(f"\n=== Debug: Getting daily progress for {phone_number} ===")
            conn = self._get_connection()
            cursor = conn.cursor()

            today = date.today().isoformat()
            print(f"\nToday's date (ISO format): {today}")

            # Progress query with totals
            if self.use_sqlite:
                # Check all meals in database (SQLite)
                cursor.execute("SELECT date, calories, protein, carbs, fat FROM meals")
                all_meals = cursor.fetchall()
                print(f"All meals: {[dict(row) for row in all_meals] if all_meals else []}")

                # Check today's meals (SQLite)
                cursor.execute("""
                    SELECT date, calories, protein, carbs, fat 
                    FROM meals 
                    WHERE phone_number = ? AND date = ?
                """, (phone_number, today))
                todays_meals = cursor.fetchall()
                print(f"\nToday's meals: {[dict(row) for row in todays_meals] if todays_meals else []}")

                # Get totals (SQLite)
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

                if result:
                    # Convert row to dict
                    result_dict = dict(result)
                    totals = {
                        "totals": {
                            "calories": float(result_dict['total_calories']),
                            "protein": float(result_dict['total_protein']),
                            "carbs": float(result_dict['total_carbs']),
                            "fat": float(result_dict['total_fat'])
                        }
                    }
                else:
                    totals = {
                        "totals": {
                            "calories": 0,
                            "protein": 0,
                            "carbs": 0,
                            "fat": 0
                        }
                    }
            else:
                # PostgreSQL version
                cursor.execute("SELECT date, calories, protein, carbs, fat FROM meals")
                all_meals = cursor.fetchall()
                print(f"All meals: {all_meals}")

                cursor.execute("""
                    SELECT date, calories, protein, carbs, fat 
                    FROM meals 
                    WHERE phone_number = %s AND date = %s
                """, (phone_number, today))
                todays_meals = cursor.fetchall()
                print(f"\nToday's meals: {todays_meals}")

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

        except Exception as e:
            print(f"Database error in get_daily_progress: {e}")
            return None
        finally:
            if conn:
                conn.close()