# Test functions to debug summary and goals separately
import sqlite3
from datetime import date


def test_summary(db_path, phone_number):
    """Test function for summary command"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        today = date.today().isoformat()

        print("\n=== Testing Summary Command ===")

        # Get today's meals
        cursor.execute("""
            SELECT meal_time, food_items, calories, protein, carbs, fat 
            FROM meals 
            WHERE phone_number = ? AND date = ?
            ORDER BY meal_time
        """, (phone_number, today))

        meals = cursor.fetchall()
        print(f"\nFound {len(meals)} meals for today:")
        for meal in meals:
            print(f"\nTime: {meal[0]}")
            print(f"Foods: {meal[1]}")
            print(f"Calories: {meal[2]}")
            print(f"Protein: {meal[3]}g")
            print(f"Carbs: {meal[4]}g")
            print(f"Fat: {meal[5]}g")

        # Get daily totals
        cursor.execute("""
            SELECT total_calories, total_protein, total_carbs, total_fat 
            FROM daily_tracking 
            WHERE phone_number = ? AND date = ?
        """, (phone_number, today))

        totals = cursor.fetchone()
        if totals:
            print("\nDaily Totals:")
            print(f"Total Calories: {totals[0]}")
            print(f"Total Protein: {totals[1]}g")
            print(f"Total Carbs: {totals[2]}g")
            print(f"Total Fat: {totals[3]}g")
        else:
            print("\nNo daily totals found")

    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def test_goals(db_path, phone_number):
    """Test function for goals command"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        today = date.today().isoformat()

        print("\n=== Testing Goals Command ===")

        # Get user goals
        cursor.execute("""
            SELECT calories, protein, carbs, fat 
            FROM user_goals 
            WHERE phone_number = ?
        """, (phone_number,))

        goals = cursor.fetchone()
        if goals:
            print("\nUser Goals:")
            print(f"Calorie Goal: {goals[0]}")
            print(f"Protein Goal: {goals[1]}g")
            print(f"Carbs Goal: {goals[2]}g")
            print(f"Fat Goal: {goals[3]}g")

            # Get current progress
            cursor.execute("""
                SELECT total_calories, total_protein, total_carbs, total_fat 
                FROM daily_tracking 
                WHERE phone_number = ? AND date = ?
            """, (phone_number, today))

            progress = cursor.fetchone()
            if progress:
                print("\nToday's Progress:")
                print(f"Calories: {progress[0]}/{goals[0]} ({(progress[0] / goals[0] * 100):.1f}%)")
                print(f"Protein: {progress[1]}/{goals[1]}g ({(progress[1] / goals[1] * 100):.1f}%)")
                print(f"Carbs: {progress[2]}/{goals[2]}g ({(progress[2] / goals[2] * 100):.1f}%)")
                print(f"Fat: {progress[3]}/{goals[3]}g ({(progress[3] / goals[3] * 100):.1f}%)")
            else:
                print("\nNo progress data found for today")
        else:
            print("\nNo goals found for user")

    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    db_path = '/Users/tfg/food-tracker-bot/src/database/database/nutrition.db'
    phone_number = 'whatsapp:+12403166242'  # Your test phone number

    test_summary(db_path, phone_number)
    test_goals(db_path, phone_number)