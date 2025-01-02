# src/services/vision_service.py
from google.cloud import vision
import os
import io


class VisionService:
    def __init__(self):
        # Initialize Vision AI client
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        credentials_path = os.path.join(project_root, 'credentials', 'google-credentials.json')

        print(f"Looking for credentials at: {credentials_path}")

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.client = vision.ImageAnnotatorClient()

        # Initialize portion and nutrition data
        self.portion_indicators = {
            'small': 0.7,
            'medium': 1.0,
            'large': 1.3,
            'extra_large': 1.6
        }

        self.food_standards = {
            'pizza': {
                'standard_portion': 200,
                'nutrition_per_100g': {
                    'calories': 266,
                    'protein': 11,
                    'carbs': 33,
                    'fat': 10
                }
            }
        }

    def analyze_local_image(self, image_path):
        try:
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # Get both label and object detection
            label_response = self.client.label_detection(image=image)
            object_response = self.client.object_localization(image=image)

            food_info = {
                'main_dish': None,
                'ingredients': [],
                'cuisine_type': None,
                'category': [],
                'confidence': 0.0,
                'portion_size': 'medium',
                'estimated_nutrition': None,
                'size_confidence': 0.0,
                'all_labels': []
            }

            # Process labels for food identification
            for label in label_response.label_annotations:
                score = label.score
                desc = label.description
                food_info['all_labels'].append({'description': desc, 'score': score})

                print(f"Processing label: {desc.lower()} with score: {score}")

                # Main dish detection (ignore generic terms)
                if score > 0.8 and desc.lower() not in ['food', 'recipe', 'ingredient']:
                    if food_info['main_dish'] is None or score > food_info['confidence']:
                        food_info['main_dish'] = desc
                        food_info['confidence'] = score

                # Ingredients detection
                if score > 0.7:
                    if any(term in desc.lower() for term in ['cheese', 'meat', 'vegetable', 'tomato', 'produce']):
                        if desc not in food_info['ingredients']:
                            food_info['ingredients'].append(desc)

                # Cuisine type detection
                if 'style' in desc.lower() or 'cuisine' in desc.lower():
                    food_info['cuisine_type'] = desc

                # Category detection
                if score > 0.7:
                    if 'fast food' in desc.lower():
                        food_info['category'].append('Fast Food')
                    elif any(term in desc.lower() for term in ['healthy', 'vegetable', 'salad']):
                        food_info['category'].append('Healthy')
                    elif any(term in desc.lower() for term in ['dessert', 'sweet', 'cake']):
                        food_info['category'].append('Dessert')

            # Estimate portion size from object detection
            if object_response.localized_object_annotations:
                food_area = 0
                for object_ in object_response.localized_object_annotations:
                    if object_.name.lower() in ['food', 'pizza', 'plate']:
                        vertices = object_.bounding_poly.normalized_vertices
                        width = abs(vertices[1].x - vertices[0].x)
                        height = abs(vertices[2].y - vertices[1].y)
                        area = width * height
                        food_area = max(food_area, area)

                if food_area > 0:
                    if food_area > 0.5:
                        food_info['portion_size'] = 'large'
                    elif food_area > 0.3:
                        food_info['portion_size'] = 'medium'
                    else:
                        food_info['portion_size'] = 'small'

                    food_info['size_confidence'] = object_.score

            # Calculate nutrition based on identified food and portion
            if food_info['main_dish']:
                food_key = food_info['main_dish'].lower()
                if food_key in self.food_standards:
                    standard = self.food_standards[food_key]
                    portion_multiplier = self.portion_indicators[food_info['portion_size']]
                    actual_portion = standard['standard_portion'] * portion_multiplier

                    food_info['estimated_nutrition'] = {
                        'portion_grams': actual_portion,
                        'calories': (standard['nutrition_per_100g']['calories'] * actual_portion) / 100,
                        'protein': (standard['nutrition_per_100g']['protein'] * actual_portion) / 100,
                        'carbs': (standard['nutrition_per_100g']['carbs'] * actual_portion) / 100,
                        'fat': (standard['nutrition_per_100g']['fat'] * actual_portion) / 100
                    }

            # Clean up results
            food_info['category'] = list(set(food_info['category']))
            food_info['ingredients'] = list(set(food_info['ingredients']))

            return food_info

        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            return None