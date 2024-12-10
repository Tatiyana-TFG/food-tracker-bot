import sqlite3
from datetime import date


def verify_database_totals(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        today = date.today().isoformat()
        phone_number = 'whatsapp:+12403166242'

        print("\n=== Database Verification ===")

        # 1. Check all meals for today
        print("\nAll meals for today:")
        cursor.execute("""
            SELECT meal_time, calories, protein, carbs, fat
            FROM meals
            WHERE date = ? AND phone_number = ?
            ORDER BY meal_time
        """, (today, phone_number))

        total_calories = 0
        meals = cursor.fetchall()
        for meal in meals:
            print(f"Time: {meal[0]}, Calories: {meal[1]}, Protein: {meal[2]}, Carbs: {meal[3]}, Fat: {meal[4]}")
            total_calories += meal[1]

        print(f"\nCalculated total calories: {total_calories}")

        # 2. Check daily_tracking table
        print("\nDaily tracking record:")
        cursor.execute("""
            SELECT total_calories, total_protein, total_carbs, total_fat
            FROM daily_tracking
            WHERE date = ? AND phone_number = ?
        """, (today, phone_number))

        tracking = cursor.fetchone()
        if tracking:
            print(
                f"Stored totals: Calories={tracking[0]}, Protein={tracking[1]}, Carbs={tracking[2]}, Fat={tracking[3]}")

        # 3. Attempt to fix totals
        cursor.execute("""
            UPDATE daily_tracking
            SET total_calories = (
                SELECT SUM(calories)
                FROM meals
                WHERE date = ? AND phone_number = ?
            ),
            total_protein = (
                SELECT SUM(protein)
                FROM meals
                WHERE date = ? AND phone_number = ?
            ),
            total_carbs = (
                SELECT SUM(carbs)
                FROM meals
                WHERE date = ? AND phone_number = ?
            ),
            total_fat = (
                SELECT SUM(fat)
                FROM meals
                WHERE date = ? AND phone_number = ?
            )
            WHERE date = ? AND phone_number = ?
        """, (today, phone_number, today, phone_number, today, phone_number, today, phone_number, today, phone_number))

        conn.commit()

        # Verify fix
        cursor.execute("""
            SELECT total_calories, total_protein, total_carbs, total_fat
            FROM daily_tracking
            WHERE date = ? AND phone_number = ?
        """, (today, phone_number))

        updated = cursor.fetchone()
        print("\nAfter fix attempt:")
        if updated:
            print(f"Updated totals: Calories={updated[0]}, Protein={updated[1]}, Carbs={updated[2]}, Fat={updated[3]}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    db_path = '/Users/tfg/food-tracker-bot/src/database/database/nutrition.db'
    verify_database_totals(db_path)