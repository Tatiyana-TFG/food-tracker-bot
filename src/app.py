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

# Dictionary to store the goal setting state for each user
goal_setting_state = {}

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

כתוב 'עזרה' בכל עת לקבלת מידע נוסף! 😊''',
    'set_calories': 'הגדר את מספר הקלוריות היומי שלך:',
    'set_protein': 'הגדר את כמות החלבון היומית שלך (בגרמים):',
    'set_carbs': 'הגדר את כמות הפחמימות היומית שלך (בגרמים):',
    'set_fat': 'הגדר את כמות השומן היומית שלך (בגרמים):',
    'macro_error': 'סך הקלוריות מהפחמימות, חלבונים ושומנים ({used_cals} קק״ל) חורג מהקלוריות היומיות שהגדרת ({total_cals} קק״ל) ב-{excess} קק״ל.\n\nמה ברצונך לעשות?\n1. להתחיל מחדש\n2. להגדיר את השלב האחרון מחדש',
    'goals_success': """✅ היעדים החדשים שלך נקבעו:

🔥 קלוריות: {actual_cals}/{calories} קק״ל
🥩 חלבון:    {protein}g ({protein_cals} קק״ל)
🌾 פחמימות: {carbs}g ({carbs_cals} קק״ל)
🥑 שומן:     {fat}g ({fat_cals} קק״ל)

שלח 'יעדים' כדי לראות את ההתקדמות שלך! 📊""",
}


# Add a helper function to calculate remaining calories
def calculate_remaining_calories(state):
    total_used = 0
    if 'protein' in state:
        total_used += state['protein'] * 4
    if 'carbs' in state:
        total_used += state['carbs'] * 4
    if 'fat' in state:
        total_used += state['fat'] * 9

    remaining = state['calories'] - total_used
    return remaining, total_used


@app.route('/')
def home():
    return "Bot is running!"


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

                            msg += f"🔥 קלוריות: {int(actual)}/{int(goal)}\n{bar}\n\n"

                        elif nutrient == 'protein':

                            msg += f"🥩 חלבון: {int(actual)}/{int(goal)} גרם\n{bar}\n\n"

                        elif nutrient == 'carbs':

                            msg += f"🌾 פחמימות: {int(actual)}/{int(goal)} גרם\n{bar}\n\n"

                        elif nutrient == 'fat':

                            msg += f"🥑 שומן: {int(actual)}/{int(goal)} גרם\n{bar}\n"

                        print(f"Generated line: {msg.splitlines()[-2]}")

                        print(f"Generated bar: {msg.splitlines()[-1]}")

                else:

                    msg = "לא נמצאו יעדים או נתוני מעקב. נסה להגדיר יעדים ולהזין ארוחות."

                print(f"Final message: {msg}")

            elif incoming_msg == 'להגדיר יעדים':
                # Start the goal setting process
                goal_setting_state[phone_number] = {'step': 'calories'}
                msg = HEBREW_MESSAGES['set_calories']

            elif phone_number in goal_setting_state and incoming_msg.isdigit():
                try:
                    value = int(incoming_msg)
                    state = goal_setting_state[phone_number]

                    if state['step'] == 'calories':
                        if value <= 0:
                            msg = "ערך הקלוריות חייב להיות חיובי. נסה שוב:"
                        else:
                            state['calories'] = value
                            state['step'] = 'protein'
                            msg = HEBREW_MESSAGES['set_protein']

                    elif state['step'] == 'protein':
                        if value < 0:
                            msg = "ערך החלבון לא יכול להיות שלילי. נסה שוב:"
                        else:
                            state['protein'] = value
                            protein_calories = value * 4
                            if protein_calories > state['calories']:
                                msg = f"ערך החלבון שהזנת ({value}g) שווה ל-{protein_calories} קלוריות, יותר מסך הקלוריות שהגדרת ({state['calories']}). נסה שוב:"
                            else:
                                state['step'] = 'carbs'
                                msg = HEBREW_MESSAGES['set_carbs']

                    elif state['step'] == 'carbs':
                        if value < 0:
                            msg = "ערך הפחמימות לא יכול להיות שלילי. נסה שוב:"
                        else:
                            state['carbs'] = value
                            remaining, used_cals = calculate_remaining_calories(state)
                            carbs_calories = value * 4

                            if remaining < 0:
                                total_cals = state['calories']
                                excess = abs(remaining)
                                msg = HEBREW_MESSAGES['macro_error'].format(
                                    used_cals=used_cals,
                                    total_cals=total_cals,
                                    excess=excess
                                )
                                state['step'] = 'error'
                            else:
                                state['step'] = 'fat'
                                msg = HEBREW_MESSAGES['set_fat']

                    elif state['step'] == 'fat':
                        if value < 0:
                            msg = "ערך השומן לא יכול להיות שלילי. נסה שוב:"
                        else:
                            state['fat'] = value
                            remaining, used_cals = calculate_remaining_calories(state)

                            if remaining < 0:
                                total_cals = state['calories']
                                excess = abs(remaining)
                                msg = HEBREW_MESSAGES['macro_error'].format(
                                    used_cals=used_cals,
                                    total_cals=total_cals,
                                    excess=excess
                                )
                                state['step'] = 'error'
                            else:
                                # Success - save goals to database
                                success = user_service.set_user_goals(
                                    phone_number,
                                    state['calories'],
                                    state['protein'],
                                    state['carbs'],
                                    state['fat']
                                )

                                if success:
                                    protein_cals = state['protein'] * 4
                                    carbs_cals = state['carbs'] * 4
                                    fat_cals = state['fat'] * 9
                                    actual_cals = protein_cals + carbs_cals + fat_cals

                                    msg = HEBREW_MESSAGES['goals_success'].format(
                                        calories=state['calories'],
                                        protein=state['protein'],
                                        carbs=state['carbs'],
                                        fat=state['fat'],
                                        protein_cals=protein_cals,
                                        carbs_cals=carbs_cals,
                                        fat_cals=fat_cals,
                                        actual_cals=actual_cals
                                    )
                                else:
                                    msg = "❌ חלה שגיאה בהגדרת היעדים. אנא נסה שוב."

                                # Clear the state now that we're done
                                del goal_setting_state[phone_number]

                    elif state['step'] == 'error':
                        # Handle error recovery
                        if incoming_msg == '1':
                            # Start over
                            goal_setting_state[phone_number] = {'step': 'calories'}
                            msg = HEBREW_MESSAGES['set_calories']
                        elif incoming_msg == '2':
                            # Retry last step
                            if 'fat' in state:
                                state['step'] = 'fat'
                                msg = HEBREW_MESSAGES['set_fat']
                            elif 'carbs' in state:
                                state['step'] = 'carbs'
                                msg = HEBREW_MESSAGES['set_carbs']
                            else:
                                # Shouldn't get here, but just in case
                                state['step'] = 'calories'
                                msg = HEBREW_MESSAGES['set_calories']
                        else:
                            msg = "אנא בחר 1 להתחיל מחדש או 2 להגדיר את השלב האחרון מחדש."

                except ValueError:
                    msg = "אנא הזן מספר בלבד."
                except Exception as e:
                    print(f"Error in goal setting: {str(e)}")
                    msg = "חלה שגיאה בהגדרת היעדים. אנא נסה שוב מהתחלה."
                    if phone_number in goal_setting_state:
                        del goal_setting_state[phone_number]

            elif phone_number in goal_setting_state and goal_setting_state[phone_number]['step'] == 'error':
                state = goal_setting_state[phone_number]
                if incoming_msg == '1':
                    # Start over
                    goal_setting_state[phone_number] = {'step': 'calories'}
                    msg = HEBREW_MESSAGES['set_calories']
                elif incoming_msg == '2':
                    # Retry last step
                    if 'fat' in state:
                        state['step'] = 'fat'
                        msg = HEBREW_MESSAGES['set_fat']
                    elif 'carbs' in state:
                        state['step'] = 'carbs'
                        msg = HEBREW_MESSAGES['set_carbs']
                    else:
                        # Shouldn't get here, but just in case
                        state['step'] = 'calories'
                        msg = HEBREW_MESSAGES['set_calories']
                else:
                    msg = "אנא בחר 1 להתחיל מחדש או 2 להגדיר את השלב האחרון מחדש."

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