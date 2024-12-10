from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from services.vision_service import VisionService
from services.nutrition_services import NutritionService
from services.user_services import UserService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize services
vision_service = VisionService()
nutrition_service = NutritionService()
user_service = UserService()

# Hebrew translations dictionary
HEBREW_MESSAGES = {
    'calories': 'קלוריות',
    'protein': 'חלבון',
    'carbs': 'פחמימות',
    'fat': 'שומן',
    'meal_logged': 'הארוחה נוספה בהצלחה! ✅',
    'analysis_failed': 'מצטער, לא הצלחתי לנתח את התמונה: ',
    'no_meals_today': 'לא נרשמו ארוחות היום! שלח לי תמונה של האוכל שלך כדי להתחיל.',
    'daily_summary': '🎯 סיכום יומי:\n\n',
    'set_goals': 'הגדר את היעדים התזונתיים היומיים שלך בפורמט הבא:\nלהגדיר יעדים קלוריות חלבון פחמימות שומן\nלדוגמה: להגדיר יעדים 2000 150 200 60',
    'goals_set': 'היעדים התזונתיים היומיים שלך עודכנו בהצלחה! 🎉',
    'invalid_goals': 'פורמט היעדים אינו תקין. אנא נסה שוב לפי ההוראות.',
    'progress_bars': '📊 התקדמות יומית:\n',
    'goal_reached': '🎉 כל הכבוד! הגעת ליעד היומי שלך עבור {nutrient}! 💪',
    'help_message': '''👋 איך אני יכול לעזור:

📸 שלח תמונת מזון: אנתח אותה ואעקוב אחר הערכים התזונתיים
📊 כתוב 'סיכום': לצפייה בסיכום התזונה היומי 
🎯 כתוב 'להגדיר יעדים': להגדרת היעדים התזונתיים היומיים שלך
📈 כתוב 'יעדים': להצגת ההתקדמות שלך ביחס ליעדים
❓ כתוב 'עזרה': להצגת הודעה זו שוב

אשמח לעזור לך לעקוב אחר המסע התזונתי שלך! 🌟''',
    'welcome_message': '''👋 היי, אני כאן כדי לעזור לך לעקוב אחר התזונה שלך! 🍎📝

אתה יכול:
📸 לשלוח לי תמונה של האוכל שלך ואני אנתח אותה  
📊 לכתוב 'סיכום' לקבלת סיכום יומי
🎯 לכתוב 'להגדיר יעדים' כדי להגדיר יעדים תזונתיים יומיים
📈 לכתוב 'יעדים' כדי לראות את ההתקדמות שלך

כתוב 'עזרה' בכל עת לקבלת מידע נוסף! 😊'''
}


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        incoming_msg = request.values.get('Body', '').lower()
        media_url = request.values.get('MediaUrl0')
        response = MessagingResponse()
        phone_number = request.values.get('From')

        # Register user if not already registered
        user_service.register_user(phone_number)

        msg = None

        if media_url:
            print(f"Received image URL: {media_url}")
            twilio_auth = (
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )

            result = vision_service.analyze_food_image(media_url, twilio_auth)

            if isinstance(result, dict) and result.get('success'):
                analysis_data = result.get('analysis')
                nutrition_data = result.get('nutrition', {})

                if analysis_data:
                    meal_data = {
                        'analysis_text': analysis_data,
                        'image_url': media_url,
                        'calories': nutrition_data.get('calories', 0),
                        'protein': nutrition_data.get('protein', 0),
                        'carbs': nutrition_data.get('carbs', 0),
                        'fat': nutrition_data.get('fat', 0),
                        'food_items': nutrition_data.get('food_items', [])
                    }

                    success = nutrition_service.log_meal(phone_number, meal_data)
                    if success:
                        msg = "🍳 ניתוח ארוחה\n"
                        msg += "──────────────\n\n"

                        # Add food items section
                        food_items = meal_data.get('food_items', [])
                        if food_items:
                            for item in food_items:
                                msg += f"• {item}\n"
                            msg += "\n"

                        # Add nutrition section with emojis and alignment
                        msg += "📊 ערכים תזונתיים:\n"
                        msg += f"🔥 קלוריות:  {meal_data['calories']} קק״ל\n"
                        msg += f"🥩 חלבון:    {meal_data['protein']} גרם\n"
                        msg += f"🌾 פחמימות: {meal_data['carbs']} גרם\n"
                        msg += f"🥑 שומן:     {meal_data['fat']} גרם\n"

                        msg += "\n──────────────\n"
                        msg += "✅ הארוחה נוספה בהצלחה!"
                    else:
                        msg = "שגיאה ברישום הארוחה. אנא נסה שוב."
                else:
                    msg = HEBREW_MESSAGES['analysis_failed'] + "התוצאה אינה תקינה."
            else:
                error_message = result.get('error', "התוצאה אינה תקינה.")
                msg = f"{HEBREW_MESSAGES['analysis_failed']}{error_message}"

        else:
            if incoming_msg == 'סיכום':
                print("\n=== Debug: Processing סיכום command ===")
                progress_data = nutrition_service.get_daily_progress(phone_number)
                print(f"Progress data received: {progress_data}")

                if progress_data and progress_data.get('totals'):
                    totals = progress_data["totals"]
                    print(f"Totals extracted: {totals}")

                    # Enhanced summary format
                    msg = "📊 סיכום יומי\n"
                    msg += "──────────────\n"

                    # Calories with emoji
                    msg += f"🔥 קלוריות: {int(totals['calories'])} קק״ל\n"

                    # Macronutrients with emojis and spacing
                    msg += f"🥩 חלבון:    {int(totals['protein'])} גרם\n"
                    msg += f"🌾 פחמימות: {int(totals['carbs'])} גרם\n"
                    msg += f"🥑 שומן:     {int(totals['fat'])} גרם\n"

                    # Add separator
                    msg += "──────────────\n"

                    # Add encouraging message based on progress
                    if totals['calories'] > 0:
                        msg += "💪 המשך כך! זוכרים לצלם את כל הארוחות"
                    else:
                        msg += "📸 צלם את הארוחה הבאה שלך כדי לעקוב אחרי התזונה"
                else:
                    msg = "לא נרשמו ארוחות היום! שלח לי תמונה של האוכל שלך כדי להתחיל. 📸"

                print(f"Final message: {msg}")

            elif incoming_msg == 'יעדים':
                print("\n=== Debug: Processing יעדים command ===")
                goals = user_service.get_user_goals(phone_number)
                progress_data = nutrition_service.get_daily_progress(phone_number)

                print(f"Goals retrieved: {goals}")
                print(f"Progress data retrieved: {progress_data}")

                if goals and progress_data and progress_data.get('totals'):
                    totals = progress_data['totals']
                    msg = HEBREW_MESSAGES['progress_bars']
                    print(f"Starting with totals: {totals}")

                    for nutrient in ['calories', 'protein', 'carbs', 'fat']:
                        goal = float(goals.get(nutrient, 0))
                        actual = float(totals.get(nutrient, 0))

                        print(f"\nDebug - {nutrient}:")
                        print(f"Actual: {actual}, Goal: {goal}")

                        percentage = (actual / goal * 100) if goal > 0 else 0
                        filled_bars = int(percentage // 10)

                        print(f"Percentage: {percentage:.1f}%")
                        print(f"Filled bars: {filled_bars}")

                        bar = '█' * filled_bars + '░' * (10 - filled_bars)

                        if nutrient == 'calories':
                            msg += f"קלוריות: {int(actual)}/{int(goal)} {bar}\n"
                        elif nutrient == 'protein':
                            msg += f"חלבון: {int(actual)}/{int(goal)} {bar}\n"
                        elif nutrient == 'carbs':
                            msg += f"פחמימות: {int(actual)}/{int(goal)} {bar}\n"
                        elif nutrient == 'fat':
                            msg += f"שומן: {int(actual)}/{int(goal)} {bar}\n"

                        print(f"Generated line: {msg.splitlines()[-1]}")
                else:
                    msg = "לא נמצאו יעדים או נתוני מעקב. נסה להגדיר יעדים ולהזין ארוחות."

                print(f"Final message: {msg}")

            elif incoming_msg.startswith('להגדיר יעדים'):
                print("\n=== Debug: Processing להגדיר יעדים command ===")
                try:
                    parts = incoming_msg.split()
                    if len(parts) == 6:  # Command word1 word2 + 4 values
                        # Parse the values
                        calories = int(parts[2])
                        protein = int(parts[3])
                        carbs = int(parts[4])
                        fat = int(parts[5])

                        print(f"Setting goals: calories={calories}, protein={protein}, carbs={carbs}, fat={fat}")

                        # Actually set the goals in the database
                        if user_service.set_user_goals(phone_number, calories, protein, carbs, fat):
                            msg = f"""✅ היעדים החדשים שלך נקבעו:

🔥 קלוריות: {calories} קק״ל
🥩 חלבון:    {protein}g
🌾 פחמימות: {carbs}g  
🥑 שומן:     {fat}g

שלח 'יעדים' כדי לראות את ההתקדמות שלך! 📊"""
                        else:
                            msg = "❌ חלה שגיאה בהגדרת היעדים. אנא נסה שוב."
                    else:
                        msg = HEBREW_MESSAGES['set_goals']  # Show the instruction message
                        print(f"Invalid format: received {len(parts)} parts instead of 6")
                except ValueError as e:
                    print(f"Value error parsing goals: {e}")
                    msg = HEBREW_MESSAGES['invalid_goals']
                except Exception as e:
                    print(f"Error setting goals: {e}")
                    msg = HEBREW_MESSAGES['invalid_goals']

            elif incoming_msg == 'עזרה':
                msg = HEBREW_MESSAGES['help_message']

            else:
                msg = HEBREW_MESSAGES['welcome_message']

        if msg is not None:
            response.message(msg)
        return str(response)

    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        response = MessagingResponse()
        response.message("מצטערים, משהו השתבש. אנא נסה שוב!")
        return str(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)