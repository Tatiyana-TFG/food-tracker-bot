# vision_service.py
import os
import requests
import base64
import re
from dotenv import load_dotenv
from openai import OpenAI


class VisionService:
    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.openai_api_key)

        self.SYSTEM_PROMPT = """You are a nutrition expert analyzing food images. For each image:
                1. List all visible food items with quantities in a clear format starting with "מנות:"
                2. Provide nutrition facts in the following format:

                מנות:
                - [food item 1 with quantity]
                - [food item 2 with quantity]

                ### ערכים תזונתיים:
                - **קלוריות**: X 
                - **חלבון**: X גרם
                - **פחמימה**: X גרם
                - **שומן**: X גרם"""

    def extract_nutrition_from_text(self, analysis_text: str) -> dict:
        """
        Extract nutrition values and food items from the Hebrew analysis text.
        """
        try:
            # Initialize default values
            nutrition = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'food_items': []
            }

            # Extract food items
            food_items = []
            capture_foods = False
            for line in analysis_text.split('\n'):
                line = line.strip()
                if 'מנות:' in line:
                    capture_foods = True
                    continue
                elif '### ערכים תזונתיים:' in line:
                    capture_foods = False
                elif capture_foods and line.startswith('-'):
                    food_item = line.strip('- ').strip()
                    if food_item:
                        food_items.append(food_item)

            nutrition['food_items'] = food_items

            # Hebrew regex patterns
            calories_match = re.search(r'\*\*קלוריות\*\*:?\s*(?:כ-)?(\d+)', analysis_text)
            if not calories_match:
                calories_match = re.search(r'קלוריות:?\s*(?:כ-)?(\d+)', analysis_text)
            if calories_match:
                nutrition['calories'] = int(calories_match.group(1))

            protein_match = re.search(r'\*\*חלבון\*\*:?\s*(?:כ-)?(\d+)', analysis_text)
            if not protein_match:
                protein_match = re.search(r'חלבון:?\s*(?:כ-)?(\d+)', analysis_text)
            if protein_match:
                nutrition['protein'] = int(protein_match.group(1))

            carbs_match = re.search(r'\*\*פחמימה\*\*:?\s*(?:כ-)?(\d+)', analysis_text)
            if not carbs_match:
                carbs_match = re.search(r'פחמימה:?\s*(?:כ-)?(\d+)', analysis_text)
            if carbs_match:
                nutrition['carbs'] = int(carbs_match.group(1))

            fat_match = re.search(r'\*\*שומן\*\*:?\s*(?:כ-)?(\d+)', analysis_text)
            if not fat_match:
                fat_match = re.search(r'שומן:?\s*(?:כ-)?(\d+)', analysis_text)
            if fat_match:
                nutrition['fat'] = int(fat_match.group(1))

            # Extract food items (lines starting with dash that don't contain nutrition info)
            food_list = []
            lines = analysis_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-'):
                    # Skip lines containing nutrition information in Hebrew
                    if not any(word in line for word in ['קלוריות', 'חלבון', 'פחמימה', 'שומן']):
                        food = line.strip('- ').strip()
                        if food:
                            food_list.append(food)

            nutrition['food_items'] = food_list

            print(f"Extracted nutrition values: {nutrition}")  # Debugging
            return nutrition

        except Exception as e:
            print(f"Error extracting nutrition values: {str(e)}")
            return {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'food_items': []
            }

    def analyze_food_image(self, image_url: str, twilio_auth: tuple) -> dict:
        try:
            # First, download the image from Twilio
            print(f"Fetching image from Twilio URL: {image_url}")
            response = requests.get(image_url, auth=twilio_auth)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch image: {response.status_code}")

            # Convert to base64
            base64_image = base64.b64encode(response.content).decode('utf-8')

            print("Sending to GPT-4o...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this food image and tell me if I'm hitting my goals"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            analysis = response.choices[0].message.content
            print(f"Analysis received: {analysis}")

            # Extract nutrition values from the analysis
            nutrition_data = self.extract_nutrition_from_text(analysis)

            return {
                'success': True,
                'analysis': analysis,
                'nutrition': nutrition_data
            }

        except Exception as e:
            print(f"Error in analyze_food_image: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }