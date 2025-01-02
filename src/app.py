from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from services.vision_service import VisionService
from services.nutrition_services import NutritionService
from services.user_services import UserService
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize services
vision_service = VisionService()
nutrition_service = NutritionService()
user_service = UserService()

# Messages dictionary for bilingual support
MESSAGES = {
    'he': {
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
        'help_message': '''👋 איך אני יכול לעזור:
            📸 שלח תמונת מזון: לניתוח אוטומטי
            📊 כתוב 'סיכום': לסיכום יומי
            🎯 כתוב 'להגדיר יעדים': להגדרת יעדים
            ❓ כתוב 'עזרה': להוראות''',
        'unauthorized': '🔒 אנא שלח את הסיסמה כדי להתחיל להשתמש בבוט.',
        'auth_success': '✅ ברוך הבא! אתה מורשה להשתמש בבוט.',
        'auth_failed': '❌ סיסמה שגויה, אנא נסה שוב.',
        'general_chat': 'היי! אני בוט שעוזר במעקב אחרי תזונה. שלח "עזרה" לקבלת רשימת הפקודות.'
    },
    'en': {
        'calories': 'Calories',
        'protein': 'Protein',
        'carbs': 'Carbs',
        'fat': 'Fat',
        'meal_logged': 'Meal logged successfully! ✅',
        'analysis_failed': 'Sorry, I could not analyze the image: ',
        'no_meals_today': 'No meals logged today! Send me a food photo to get started.',
        'daily_summary': '🎯 Daily Summary:\n\n',
        'set_goals': 'Set your daily nutritional goals using the format:\nset goals calories protein carbs fat\nExample: set goals 2000 150 200 60',
        'goals_set': 'Your daily nutritional goals have been updated successfully! 🎉',
        'invalid_goals': 'Invalid goals format. Please try again following the instructions.',
        'help_message': '''👋 How can I help:
            📸 Send food photo: for automatic analysis
            📊 Type 'summary': for daily summary
            🎯 Type 'set goals': to set goals
            ❓ Type 'help': for instructions''',
        'unauthorized': '🔒 Please send the password to start using the bot.',
        'auth_success': '✅ Welcome! You are authorized to use the bot.',
        'auth_failed': '❌ Incorrect password, please try again.',
        'general_chat': "Hi! I'm a nutrition tracking bot. Send 'help' for a list of commands."
    }
}


def detect_language(text):
    """Detect if the message is in English or Hebrew"""
    # Simple detection based on ASCII characters
    if text and all(ord(char) < 128 for char in text):
        return 'en'
    return 'he'

@app.route('/')
def home():
    return "Bot is running!"
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        incoming_msg = request.values.get('Body', '').lower()
        media_url = request.values.get('MediaUrl0')
        phone_number = request.values.get('From')

        response = MessagingResponse()
        lang = detect_language(incoming_msg)
        msgs = MESSAGES[lang]

        # Handle password authorization
        if incoming_msg == '3233':
            result = user_service.register_user(phone_number, password='3233')
            response.message(msgs['auth_success'] if result['status'] == 'success' else msgs['auth_failed'])
            return str(response)

        # Check authorization for all other requests
        auth_check = user_service.get_user_goals(phone_number)
        if auth_check['status'] == 'error' and 'not authorized' in auth_check['message']:
            response.message(msgs['unauthorized'])
            return str(response)

        # Handle media (food photos)
        if media_url:
            print(f"Received image URL: {media_url}")
            twilio_auth = (os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
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
                    msg = f"{analysis_data}\n\n{msgs['meal_logged']}" if success else "Error logging meal. Please try again."
                else:
                    msg = msgs['analysis_failed'] + "Invalid result."
            else:
                error_message = result.get('error', "Invalid result.")
                msg = f"{msgs['analysis_failed']}{error_message}"

        # Handle text commands
        else:
            # English commands
            if lang == 'en':
                if incoming_msg == 'summary':
                    progress_data = nutrition_service.get_daily_progress(phone_number)
                    if progress_data:
                        totals = progress_data["totals"]
                        msg = msgs['daily_summary']
                        msg += f"{msgs['calories']}: {totals['calories']} kcal\n"
                        msg += f"{msgs['protein']}: {totals['protein']}g\n"
                        msg += f"{msgs['carbs']}: {totals['carbs']}g\n"
                        msg += f"{msgs['fat']}: {totals['fat']}g\n\n"
                    else:
                        msg = msgs['no_meals_today']

                elif incoming_msg.startswith('set goals'):
                    try:
                        parts = incoming_msg.split()
                        calories, protein, carbs, fat = map(int, parts[-4:])
                        user_service.set_user_goals(phone_number, calories, protein, carbs, fat)
                        msg = msgs['goals_set']
                    except:
                        msg = msgs['invalid_goals']

                elif incoming_msg == 'help':
                    msg = msgs['help_message']

                else:
                    msg = msgs['general_chat']

            # Hebrew commands
            else:
                if incoming_msg == 'סיכום':
                    progress_data = nutrition_service.get_daily_progress(phone_number)
                    if progress_data:
                        totals = progress_data["totals"]
                        msg = msgs['daily_summary']
                        msg += f"{msgs['calories']}: {totals['calories']} kcal\n"
                        msg += f"{msgs['protein']}: {totals['protein']}g\n"
                        msg += f"{msgs['carbs']}: {totals['carbs']}g\n"
                        msg += f"{msgs['fat']}: {totals['fat']}g\n\n"
                    else:
                        msg = msgs['no_meals_today']

                elif incoming_msg.startswith('להגדיר יעדים'):
                    try:
                        parts = incoming_msg.split()
                        calories, protein, carbs, fat = map(int, parts[-4:])
                        user_service.set_user_goals(phone_number, calories, protein, carbs, fat)
                        msg = msgs['goals_set']
                    except:
                        msg = msgs['invalid_goals']

                elif incoming_msg == 'עזרה':
                    msg = msgs['help_message']

                else:
                    msg = msgs['general_chat']

        response.message(msg)
        return str(response)

    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        response = MessagingResponse()
        response.message(
            "Sorry, something went wrong. Please try again!" if lang == 'en' else "מצטערים, משהו השתבש. אנא נסה שוב!")
        return str(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)