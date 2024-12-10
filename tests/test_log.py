import sys
import os
import json
import sqlite3

# Add the parent directory to the Python path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.nutrition_services import NutritionService


def test_log_meal():
    nutrition_service = NutritionService()

    # Test data
    phone_number = "+1234567890"
    meal_data = {
        "food_items": ["Test Cookie"],
        "portion_size": "1 cookie",
        "calories": "200",
        "protein": "2",
        "carbs": "30",
        "fat": "10",
        "health_insight": "Test health insight",
        "analysis_text": "Test analysis text"
    }

    # Log the meal
    success = nutrition_service.log_meal_from_analysis(phone_number, meal_data)

    if success:
        print("Meal logged successfully!")
    else:
        print("Failed to log meal.")

    # Verify the logged meal
    meals = nutrition_service.get_daily_meals(phone_number)
    if meals:
        print("Retrieved meals:")
        for meal in meals:
            print(json.dumps(meal, indent=2))
    else:
        print("No meals found for the given phone number today.")

    # Print all meals in the database for debugging
    print("\nAll meals in database:")
    conn = sqlite3.connect(nutrition_service.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals")
    all_meals = cursor.fetchall()
    for meal in all_meals:
        print(meal)
    conn.close()


if __name__ == "__main__":
    test_log_meal()