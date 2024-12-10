# src/services/vision_service.py
from google.cloud import vision
import os


class VisionService:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        credentials_path = os.path.join(project_root, 'credentials', 'google-credentials.json')

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.client = vision.ImageAnnotatorClient()

    def analyze_image_from_url(self, image_url):
        try:
            image = vision.Image()
            image.source.image_uri = image_url

            response = self.client.label_detection(image=image)

            # Just get the food-related labels for now
            food_labels = []
            for label in response.label_annotations:
                print(f"Found label: {label.description} with score: {label.score}")
                if label.score > 0.7:  # Confidence threshold
                    food_labels.append(label.description)

            return food_labels

        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            return None